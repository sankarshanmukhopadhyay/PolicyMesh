from datetime import datetime, timezone
from pathlib import Path

from links.action_decisions import ActionPolicy, evaluate_action, load_json, verify_action_receipt

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "travel-hospitality"


def _run(name: str):
    expected = load_json(EXAMPLE / "expected" / f"{name}.json")
    policy = ActionPolicy.model_validate(load_json(EXAMPLE / "policy" / "corporate-hotel-booking.action-policy.json"))
    request = load_json(EXAMPLE / "requests" / f"{name}.json")
    evidence = load_json(EXAMPLE / "evidence" / "base.json")
    authority = load_json(EXAMPLE / "authority" / expected["authority"])
    receipt = evaluate_action(policy, request, evidence, authority, now=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc))
    return expected, receipt


def test_travel_example_scenarios_match_expected_decisions():
    for expected_file in sorted((EXAMPLE / "expected").glob("*.json")):
        expected, receipt = _run(expected_file.stem)
        assert receipt.decision == expected["decision"]
        assert verify_action_receipt(receipt)


def test_permit_has_all_rules_passed_reason():
    _, receipt = _run("permitted-booking")
    assert receipt.decision == "permit"
    assert receipt.reason_codes == ["all_applicable_rules_passed"]
    assert all(row.result == "pass" for row in receipt.evaluations)


def test_repricing_defers_for_additional_authority():
    _, receipt = _run("supplier-repriced")
    assert receipt.decision == "defer"
    assert "manager_approval_required" in receipt.reason_codes


def test_revoked_mandate_fails_closed():
    _, receipt = _run("revoked-mandate")
    assert receipt.decision == "deny"
    assert "mandate_not_active" in receipt.reason_codes
