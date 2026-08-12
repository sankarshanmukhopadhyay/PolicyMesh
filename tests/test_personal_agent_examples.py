from datetime import datetime, timezone
from pathlib import Path
import pytest
from links.action_decisions import ActionPolicy, evaluate_action, load_json, verify_action_receipt
ROOT=Path(__file__).resolve().parents[1]
EXAMPLES=["personal-shopping","healthcare-agent","insurance-claim-agent"]
@pytest.mark.parametrize("example_name", EXAMPLES)
def test_personal_agent_scenarios_match_expected(example_name):
    example=ROOT/"examples"/example_name
    for expected_file in sorted((example/"expected").glob("*.json")):
        expected=load_json(expected_file)
        request=load_json(example/"requests"/f"{expected_file.stem}.json")
        evidence=load_json(example/"evidence"/expected.get("evidence","base.json"))
        authority=load_json(example/"authority"/expected.get("authority","active-mandate.json"))
        policy=ActionPolicy.model_validate(load_json(example/"policy"/expected["policy"]))
        receipt=evaluate_action(policy,request,evidence,authority,now=datetime(2026,8,12,12,0,tzinfo=timezone.utc))
        assert receipt.decision==expected["decision"], (example_name,expected_file.stem,receipt.reason_codes)
        assert verify_action_receipt(receipt)

def test_healthcare_consent_changes_defer_to_permit():
    ex=ROOT/"examples"/"healthcare-agent"
    policy=ActionPolicy.model_validate(load_json(ex/"policy"/"disclosure.action-policy.json"))
    req=load_json(ex/"requests"/"genetic-data-consent-required.json")
    auth=load_json(ex/"authority"/"active-mandate.json")
    before=evaluate_action(policy,req,load_json(ex/"evidence"/"base.json"),auth)
    after=evaluate_action(policy,req,load_json(ex/"evidence"/"with-genetic-consent.json"),auth)
    assert before.decision=="defer"
    assert after.decision=="permit"

def test_insurance_large_settlement_escalates_not_denies():
    ex=ROOT/"examples"/"insurance-claim-agent"
    policy=ActionPolicy.model_validate(load_json(ex/"policy"/"settlement.action-policy.json"))
    receipt=evaluate_action(policy,load_json(ex/"requests"/"settlement-approval-required.json"),load_json(ex/"evidence"/"base.json"),load_json(ex/"authority"/"active-mandate.json"))
    assert receipt.decision=="defer"
    assert "principal_approval_required" in receipt.reason_codes
