from datetime import datetime, timezone
import pytest
from links.action_decisions import ActionPolicy, evaluate_action, verify_action_receipt

NOW = datetime(2026, 8, 12, tzinfo=timezone.utc)

def policy(operator, **kw):
    rule = dict(rule_id="r", description="constraint", source="request",
                path="value", operator=operator, reason_code="constraint", **kw)
    return ActionPolicy(policy_id="p", version="1", title="test", rules=[rule])

def request(**kw):
    return dict(request_id="r", action="commit", **kw)

@pytest.mark.parametrize("operator,expected", [
    ("eq", "x"), ("neq", "x"), ("in", ["x"]), ("not_in", ["x"]),
    ("lt", 2), ("lte", 2), ("gt", 2), ("gte", 2)])
def test_missing_and_null_never_pass(operator, expected):
    for data, kind in [(request(), "missing_operand"), (request(value=None), "null_operand")]:
        receipt = evaluate_action(policy(operator, expected=expected), data, now=NOW)
        assert receipt.decision == "deny"
        assert receipt.evaluations[0].failure_kind == kind
        assert verify_action_receipt(receipt)

def test_missing_both_sides_and_defer():
    p = policy("eq", expected_path="evidence.value", on_fail="defer")
    assert evaluate_action(p, request(), now=NOW).decision == "defer"

@pytest.mark.parametrize("operator,actual,expected", [
    ("eq", 1, True), ("neq", 1, True), ("lte", False, 2),
    ("not_in", 1, ["1"]), ("in", True, [1])])
def test_incompatible_operands_fail(operator, actual, expected):
    assert evaluate_action(policy(operator, expected=expected), request(value=actual), now=NOW).decision == "deny"

def test_invalid_policies_and_mutated_policy():
    with pytest.raises(ValueError):
        ActionPolicy(policy_id="p", version="1", title="test", rules=[])
    with pytest.raises(ValueError):
        policy("in", expected="substring")
    p = policy("eq", expected=True)
    p.rules.clear()
    with pytest.raises(ValueError):
        evaluate_action(p, request(value=True), now=NOW)

def test_invalid_envelope():
    with pytest.raises(ValueError):
        evaluate_action(policy("exists"), {"value": 1}, now=NOW)
    with pytest.raises(ValueError):
        evaluate_action(policy("exists"), request(value=float("nan")), now=NOW)

def test_exists_and_precedence():
    p = policy("exists", on_fail="defer")
    assert evaluate_action(p, request(), now=NOW).decision == "defer"
    assert evaluate_action(p, request(value=False), now=NOW).decision == "permit"
    p.rules.append(policy("eq", expected="x").rules[0].model_copy(update={"rule_id": "deny"}))
    assert evaluate_action(p, request(), now=NOW).decision == "deny"
