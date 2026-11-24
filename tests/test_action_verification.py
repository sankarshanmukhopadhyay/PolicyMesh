from datetime import datetime, timezone
from links.sdk import ActionPolicy, evaluate_action, verify_action_decision
from links.action_decisions import verify_action_receipt
from links.utils import canonical_json, sha256_hex

def inputs():
    policy = ActionPolicy(policy_id="p", version="1", title="test", rules=[
        dict(rule_id="r", description="active", source="authority_context",
             path="active", operator="eq", expected=True, reason_code="inactive")])
    return policy, {"request_id": "r", "action": "commit"}, {}, {"active": True}

def rehash(receipt, historical=False):
    data = receipt.model_dump(mode="json")
    data.pop("receipt_id")
    if historical:
        data.pop("evaluation_semantics")
        for row in data["evaluations"]:
            row.pop("failure_kind")
    data["decided_at"] = receipt.decided_at.isoformat().replace("+00:00", "Z")
    return receipt.model_copy(update={"receipt_id": sha256_hex(canonical_json(data))})

def test_reproduction_and_limits():
    args = inputs()
    receipt = evaluate_action(*args, now=datetime(2026, 8, 12, tzinfo=timezone.utc))
    result = verify_action_decision(receipt, *args)
    assert result.overall == "verified"
    assert result.issuer_authentication == result.authority_validation == "not_checked"
    assert verify_action_decision(receipt, *args[:3]).overall == "incomplete"
    assert verify_action_decision(receipt, *args[:3], {"active": False}).input_binding == "fail"
    forged = receipt.model_copy(update={"decision": "deny"})
    assert verify_action_decision(forged, *args).receipt_integrity == "fail"
    forged = rehash(forged)
    assert verify_action_receipt(forged)
    result = verify_action_decision(forged, *args)
    assert result.input_binding == "pass" and result.decision_reproduction == "fail"

def test_historical_receipt_integrity_only():
    args = inputs()
    receipt = evaluate_action(*args).model_copy(update={"evaluation_semantics": None})
    receipt = rehash(receipt, historical=True)
    assert verify_action_receipt(receipt)
    assert verify_action_decision(receipt, *args).overall == "incomplete"


def test_receipt_rejects_unknown_rule_evidence():
    import pytest
    from links.action_decisions import ActionDecisionReceipt
    receipt = evaluate_action(*inputs()).model_dump(mode="json")
    receipt["evaluations"][0]["unverified_authority"] = True
    with pytest.raises(ValueError):
        ActionDecisionReceipt.model_validate(receipt)
