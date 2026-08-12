from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .utils import canonical_json, sha256_hex


ACTION_POLICY_FORMAT = "policymesh.action_policy.v1"
ACTION_RECEIPT_FORMAT = "policymesh.action_decision_receipt.v1"

Decision = Literal["permit", "deny", "defer"]
Operator = Literal["eq", "neq", "lt", "lte", "gt", "gte", "in", "not_in", "exists"]
Source = Literal["request", "evidence", "authority_context"]


class ActionRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    description: str
    source: Source
    path: str
    operator: Operator
    expected: Any = None
    expected_path: Optional[str] = None
    on_fail: Literal["deny", "defer"] = "deny"
    reason_code: str

    @model_validator(mode="after")
    def validate_expected(self) -> "ActionRule":
        if self.operator == "exists":
            return self
        if self.expected_path is None and self.expected is None:
            raise ValueError("rule requires expected or expected_path unless operator=exists")
        if self.expected_path is not None and self.expected is not None:
            raise ValueError("rule must use expected or expected_path, not both")
        return self


class ActionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: str = ACTION_POLICY_FORMAT
    policy_id: str
    version: str
    title: str
    description: str = ""
    rules: List[ActionRule]


class RuleEvaluation(BaseModel):
    rule_id: str
    description: str
    result: Literal["pass", "fail"]
    actual: Any = None
    expected: Any = None
    operator: Operator
    on_fail: Literal["deny", "defer"]
    reason_code: str


class ActionDecisionReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: str = ACTION_RECEIPT_FORMAT
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


def _get_path(obj: Any, path: str) -> Any:
    current = obj
    for part in path.split(".") if path else []:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _compare(actual: Any, expected: Any, operator: Operator) -> bool:
    if operator == "exists":
        return actual is not None
    if operator == "eq":
        return actual == expected
    if operator == "neq":
        return actual != expected
    if operator == "in":
        return actual in expected if isinstance(expected, (list, tuple, set, str)) else False
    if operator == "not_in":
        return actual not in expected if isinstance(expected, (list, tuple, set, str)) else False
    if actual is None or expected is None:
        return False
    try:
        if operator == "lt":
            return actual < expected
        if operator == "lte":
            return actual <= expected
        if operator == "gt":
            return actual > expected
        if operator == "gte":
            return actual >= expected
    except TypeError:
        return False
    return False


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
    evidence = evidence or {}
    authority_context = authority_context or {}
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
        passed = _compare(actual, expected, rule.operator)
        evaluations.append(
            RuleEvaluation(
                rule_id=rule.rule_id,
                description=rule.description,
                result="pass" if passed else "fail",
                actual=actual,
                expected=expected,
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

    ts = now or datetime.now(timezone.utc)
    p_hash = policy_hash(policy)
    request_digest = sha256_hex(canonical_json(request))
    evidence_digest = sha256_hex(canonical_json(evidence))
    authority_digest = sha256_hex(canonical_json(authority_context))
    seed = {
        "format": ACTION_RECEIPT_FORMAT,
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
    seed["decided_at"] = receipt.decided_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return claimed == sha256_hex(canonical_json(seed))


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_action_receipt(path: Path, receipt: ActionDecisionReceipt) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(receipt.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path
