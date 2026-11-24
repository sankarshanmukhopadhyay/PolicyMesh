from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .utils import canonical_json, sha256_hex


ACTION_POLICY_FORMAT = "policymesh.action_policy.v1"
ACTION_RECEIPT_FORMAT = "policymesh.action_decision_receipt.v1"
ACTION_SEMANTICS = "policymesh.action_evaluation.v2"
_MISSING = object()

Decision = Literal["permit", "deny", "defer"]
Operator = Literal["eq", "neq", "lt", "lte", "gt", "gte", "in", "not_in", "exists"]
Source = Literal["request", "evidence", "authority_context"]


class ActionRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(min_length=1)
    description: str
    source: Source
    path: str = Field(min_length=1)
    operator: Operator
    expected: Any = None
    expected_path: Optional[str] = None
    on_fail: Literal["deny", "defer"] = "deny"
    reason_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_expected(self) -> "ActionRule":
        if any(not part for part in self.path.split(".")):
            raise ValueError("path must contain nonempty segments")
        if self.expected_path is not None:
            parts = self.expected_path.split(".")
            if len(parts) < 2 or parts[0] not in ("request", "evidence", "authority_context") or any(not p for p in parts):
                raise ValueError("expected_path must identify a contextual field")
        if self.operator == "exists":
            if self.expected is not None or self.expected_path is not None:
                raise ValueError("exists does not accept an expected operand")
            return self
        if self.expected_path is None and self.expected is None:
            raise ValueError("rule requires a non-null expected or expected_path")
        if self.expected_path is not None and self.expected is not None:
            raise ValueError("rule must use expected or expected_path, not both")
        if self.expected_path is None:
            _validate_json(self.expected)
            if self.operator in ("in", "not_in") and not isinstance(self.expected, list):
                raise ValueError("membership requires an array")
            if self.operator in ("lt", "lte", "gt", "gte") and not _number(self.expected):
                raise ValueError("ordering requires a finite number")
        return self


class ActionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: Literal["policymesh.action_policy.v1"] = ACTION_POLICY_FORMAT
    policy_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    rules: List[ActionRule] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_rules(self) -> "ActionPolicy":
        if len({r.rule_id for r in self.rules}) != len(self.rules):
            raise ValueError("rule identifiers must be unique")
        return self


class RuleEvaluation(BaseModel):
    rule_id: str
    description: str
    result: Literal["pass", "fail"]
    actual: Any = None
    expected: Any = None
    operator: Operator
    on_fail: Literal["deny", "defer"]
    reason_code: str
    failure_kind: Optional[Literal["missing_operand", "null_operand", "invalid_operand", "constraint_failed"]] = None


class ActionDecisionReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: Literal["policymesh.action_decision_receipt.v1"] = ACTION_RECEIPT_FORMAT
    receipt_id: str
    decided_at: datetime
    decision: Decision
    request_id: str
    action: str
    principal: Optional[str] = None
    actor: Optional[str] = None
    policy_id: str
    policy_version: str
    policy_hash: str
    request_digest: str
    evidence_digest: str
    authority_context_digest: str
    reason_codes: List[str] = Field(default_factory=list)
    evaluations: List[RuleEvaluation] = Field(default_factory=list)
    evaluation_semantics: Optional[Literal["policymesh.action_evaluation.v2"]] = None


def _number(value: Any) -> bool:
    return type(value) is int or (type(value) is float and math.isfinite(value))


def _validate_json(value: Any) -> None:
    if value is None or type(value) in (str, bool) or _number(value):
        return
    if type(value) is list:
        for item in value:
            _validate_json(item)
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for item in value.values():
            _validate_json(item)
        return
    raise ValueError("inputs must contain only finite JSON values")


def _get_path(obj: Any, path: str) -> Any:
    current = obj
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return _MISSING
    return current


def _compatible(a: Any, b: Any) -> bool:
    return (_number(a) and _number(b)) or type(a) is type(b)


def _equal(a: Any, b: Any) -> bool:
    if not _compatible(a, b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_equal(a[k], b[k]) for k in a)
    return a == b


def _failure(actual: Any, expected: Any, operator: Operator) -> Optional[str]:
    if actual is _MISSING or (operator != "exists" and expected is _MISSING):
        return "missing_operand"
    if actual is None or (operator != "exists" and expected is None):
        return "null_operand"
    if operator == "exists":
        return None
    if operator in ("eq", "neq"):
        if not _compatible(actual, expected):
            return "invalid_operand"
        passed = _equal(actual, expected)
        if operator == "neq":
            passed = not passed
    elif operator in ("in", "not_in"):
        if not isinstance(expected, list) or any(x is None or not _compatible(actual, x) for x in expected):
            return "invalid_operand"
        passed = any(_equal(actual, x) for x in expected)
        if operator == "not_in":
            passed = not passed
    else:
        if not (_number(actual) and _number(expected)):
            return "invalid_operand"
        passed = {"lt": actual < expected, "lte": actual <= expected,
                  "gt": actual > expected, "gte": actual >= expected}[operator]
    return None if passed else "constraint_failed"


def policy_hash(policy: ActionPolicy) -> str:
    return sha256_hex(canonical_json(policy.model_dump(mode="json")))


def evaluate_action(
    policy: ActionPolicy,
    request: Dict[str, Any],
    evidence: Optional[Dict[str, Any]] = None,
    authority_context: Optional[Dict[str, Any]] = None,
    *,
    now: Optional[datetime] = None,
) -> ActionDecisionReceipt:
    policy = ActionPolicy.model_validate(policy.model_dump(mode="python"))
    evidence = {} if evidence is None else evidence
    authority_context = {} if authority_context is None else authority_context
    for value in (request, evidence, authority_context):
        if type(value) is not dict:
            raise ValueError("request, evidence and authority_context must be JSON objects")
        _validate_json(value)
    for key in ("request_id", "action"):
        if not isinstance(request.get(key), str) or not request[key].strip():
            raise ValueError(f"request requires nonempty {key}")
    for key in ("principal", "actor"):
        if request.get(key) is not None and not isinstance(request[key], str):
            raise ValueError(f"{key} must be a string or null")
    ts = now or datetime.now(timezone.utc)
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ValueError("decision time must be timezone-aware")
    ts = ts.astimezone(timezone.utc)
    contexts = {
        "request": request,
        "evidence": evidence,
        "authority_context": authority_context,
    }
    combined = contexts
    evaluations: List[RuleEvaluation] = []
    failed_deny: List[str] = []
    failed_defer: List[str] = []

    for rule in policy.rules:
        actual = _get_path(contexts[rule.source], rule.path)
        expected = _get_path(combined, rule.expected_path) if rule.expected_path else rule.expected
        failure = _failure(actual, expected, rule.operator)
        passed = failure is None
        evaluations.append(
            RuleEvaluation(
                rule_id=rule.rule_id,
                description=rule.description,
                result="pass" if passed else "fail",
                actual=None if actual is _MISSING else actual,
                expected=None if expected is _MISSING else expected,
                failure_kind=failure,
                operator=rule.operator,
                on_fail=rule.on_fail,
                reason_code=rule.reason_code,
            )
        )
        if not passed:
            (failed_deny if rule.on_fail == "deny" else failed_defer).append(rule.reason_code)

    if failed_deny:
        decision: Decision = "deny"
        reasons = failed_deny + [r for r in failed_defer if r not in failed_deny]
    elif failed_defer:
        decision = "defer"
        reasons = failed_defer
    else:
        decision = "permit"
        reasons = ["all_applicable_rules_passed"]

    p_hash = policy_hash(policy)
    request_digest = sha256_hex(canonical_json(request))
    evidence_digest = sha256_hex(canonical_json(evidence))
    authority_digest = sha256_hex(canonical_json(authority_context))
    seed = {
        "format": ACTION_RECEIPT_FORMAT,
        "evaluation_semantics": ACTION_SEMANTICS,
        "decided_at": ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "decision": decision,
        "request_id": str(request.get("request_id", "unknown")),
        "action": str(request.get("action", "unknown")),
        "principal": request.get("principal"),
        "actor": request.get("actor"),
        "policy_id": policy.policy_id,
        "policy_version": policy.version,
        "policy_hash": p_hash,
        "request_digest": request_digest,
        "evidence_digest": evidence_digest,
        "authority_context_digest": authority_digest,
        "reason_codes": reasons,
        "evaluations": [e.model_dump(mode="json") for e in evaluations],
    }
    receipt_id = sha256_hex(canonical_json(seed))
    return ActionDecisionReceipt(receipt_id=receipt_id, decided_at=ts, **{k: v for k, v in seed.items() if k not in {"format", "decided_at"}})


def verify_action_receipt(receipt: ActionDecisionReceipt) -> bool:
    seed = receipt.model_dump(mode="json")
    claimed = seed.pop("receipt_id")
    if receipt.evaluation_semantics is None:
        seed.pop("evaluation_semantics")
        for row in seed["evaluations"]:
            if row.pop("failure_kind") is not None:
                return False
    seed["decided_at"] = receipt.decided_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return claimed == sha256_hex(canonical_json(seed))


def load_json(path: Path) -> Dict[str, Any]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    if type(value) is not dict:
        raise ValueError("expected a JSON object")
    _validate_json(value)
    return value


def write_action_receipt(path: Path, receipt: ActionDecisionReceipt) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(receipt.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path
