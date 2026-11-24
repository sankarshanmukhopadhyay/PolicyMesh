"""Executable contract vectors; run via pytest or the evidence workflow."""
import json
from pathlib import Path
from datetime import datetime, timezone
import pytest
from jsonschema import Draft202012Validator
from typer.testing import CliRunner
from links.cli import app
from links.sdk import ActionPolicy, evaluate_action, verify_action_decision
from links.action_decisions import ActionDecisionReceipt, load_json

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests/fixtures/action_conformance/vectors.json").read_text())
NOW = datetime(2026, 8, 12, tzinfo=timezone.utc)

def schema(name):
    return Draft202012Validator(load_json(ROOT / "schemas" / (name + ".schema.json")))

def document(case):
    return {"format":"policymesh.action_policy.v1", "policy_id":"conformance", "version":"1",
            "title":"fixture", "rules":[case["rule"]]}

@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_action_contract(case):
    doc = document(case)
    schema("action_policy").validate(doc)
    receipt = evaluate_action(ActionPolicy.model_validate(doc), case["request"], {}, {}, now=NOW)
    assert receipt.decision == case["decision"]
    assert receipt.evaluations[0].failure_kind == case["failure_kind"]
    schema("action_decision_receipt").validate(receipt.model_dump(mode="json"))
    report = verify_action_decision(receipt, ActionPolicy.model_validate(doc), case["request"], {}, {})
    schema("action_verification").validate(report.model_dump(mode="json"))
    assert report.overall == "verified"

@pytest.mark.parametrize("case", [CASES[0], CASES[3], CASES[5]], ids=["PM-CLI-001","PM-CLI-002","PM-CLI-003"])
def test_cli_sdk_parity(case, tmp_path):
    paths = [tmp_path / (name + ".json") for name in ("policy","request","evidence","authority","receipt")]
    for path, value in zip(paths, (document(case),case["request"],{},{})):
        path.write_text(json.dumps(value))
    p, q, e, a, receipt_path = map(str, paths)
    runner = CliRunner()
    result = runner.invoke(app, ["action","evaluate",p,q,e,"--authority-context",a,"--out",receipt_path])
    assert result.exit_code == 0, result.output
    receipt = ActionDecisionReceipt.model_validate(load_json(paths[-1]))
    sdk = evaluate_action(ActionPolicy.model_validate(document(case)),case["request"],{}, {},now=receipt.decided_at)
    assert sdk.receipt_id == receipt.receipt_id
    result = runner.invoke(app, ["action","verify-decision",receipt_path,p,q,e,a])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["overall"] == "verified"
    paths[2].write_text('{"changed":true}')
    result = runner.invoke(app, ["action","verify-decision",receipt_path,p,q,e,a])
    assert result.exit_code != 0

def test_PM_SCHEMA_001():
    doc = document(CASES[0])
    doc["rules"] = []
    assert not schema("action_policy").is_valid(doc)
    with pytest.raises(ValueError):
        ActionPolicy.model_validate(doc)


@pytest.mark.parametrize("operator", ["in", "not_in", "lt", "lte", "gt", "gte"])
def test_contextual_operand_schema_roundtrip(operator):
    doc = document(CASES[0])
    doc["rules"][0].update(operator=operator, expected=None, expected_path="evidence.limit")
    schema("action_policy").validate(doc)
    policy = ActionPolicy.model_validate(doc)
    schema("action_policy").validate(policy.model_dump(mode="json"))
