"""Exercise every published scenario through its actual offline runner."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from links.action_decisions import ActionDecisionReceipt, ActionPolicy, load_json, verify_action_decision

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ("travel-hospitality", "personal-shopping", "healthcare-agent", "insurance-claim-agent")
PIN = "1eda75842cf3b268361dc47ce8ade23b6a99c5cb"

def index(domain):
    return load_json(ROOT / "examples" / domain / "scenarios.json")

CASES = [(domain, row["id"]) for domain in DOMAINS for row in index(domain)["scenarios"]]

@pytest.mark.parametrize("domain", DOMAINS)
def test_index_exactly_covers_fixtures(domain):
    ex = ROOT / "examples" / domain
    doc = index(domain)
    assert doc["domain"] == domain and doc["dtfc_revision"] == PIN
    ids = [row["id"] for row in doc["scenarios"]]
    assert len(ids) == len(set(ids))
    assert set(ids) == {p.stem for p in (ex / "requests").glob("*.json")}
    assert set(ids) == {p.stem for p in (ex / "expected").glob("*.json")}
    for row in doc["scenarios"]:
        assert row["request"] == f"requests/{row['id']}.json"
        assert row["expected"] == f"expected/{row['id']}.json"
        assert row["decision"] == load_json(ex / row["expected"])["decision"]
        assert row["rationale"]
        for mapping in row["correlations"]:
            assert mapping["relationship"] == "illustrates"
            assert mapping["case_version"] == "0.1.0"
            assert f"/blob/{PIN}/corpus/" in mapping["source"]
            assert mapping["source"].endswith(f"/{mapping['case_id']}.json")
            assert mapping["limit"]

@pytest.mark.parametrize("domain,scenario", CASES, ids=[f"{d}/{s}" for d,s in CASES])
def test_actual_runner_and_retained_inputs(domain, scenario):
    ex = ROOT / "examples" / domain
    result = subprocess.run([sys.executable, str(ex / "run.py"), scenario], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    expected = load_json(ex / "expected" / f"{scenario}.json")
    request = load_json(ex / "requests" / f"{scenario}.json")
    policy = ActionPolicy.model_validate(load_json(ex / "policy" / expected.get("policy", "corporate-hotel-booking.action-policy.json")))
    evidence = load_json(ex / "evidence" / expected.get("evidence", "base.json"))
    authority = load_json(ex / "authority" / expected.get("authority", "active-mandate.json"))
    receipt = ActionDecisionReceipt.model_validate(load_json(ex / "artifacts" / f"{scenario}.receipt.json"))
    assert receipt.decision == expected["decision"]
    if expected.get("required_reason"):
        assert expected["required_reason"] in receipt.reason_codes
    verification = verify_action_decision(receipt, policy, request, evidence, authority)
    assert verification.overall == "verified"
    assert verification.authority_validation == "not_checked"
    assert load_json(ex / "artifacts" / f"{scenario}.receipt.verification.json") == verification.model_dump(mode="json")

def test_resolution_changes_evidence_not_authority():
    ex = ROOT / "examples" / "insurance-claim-agent"
    before = load_json(ex / "requests" / "missing-evidence.json")
    after = load_json(ex / "requests" / "payment-evidence-resolved.json")
    assert before["request_id"] == after["request_id"]
    before["claim"]["evidence"]["payment_receipt"] = True
    assert before == after
    a = load_json(ex / "expected" / "missing-evidence.json")
    b = load_json(ex / "expected" / "payment-evidence-resolved.json")
    assert a["authority"] == b["authority"] and a["policy"] == b["policy"]
    assert a["decision"] == "defer" and b["decision"] == "permit"
