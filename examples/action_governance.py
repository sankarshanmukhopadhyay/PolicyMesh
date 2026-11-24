"""Offline example: the application owns the side-effect boundary."""
from links.sdk import ActionPolicy, evaluate_action, verify_action_decision

POLICY = ActionPolicy(policy_id="purchase", version="1", title="Bounded purchase", rules=[
    dict(rule_id="active",description="active mandate",source="authority_context",path="active",
         operator="eq",expected=True,reason_code="inactive"),
    dict(rule_id="limit",description="spending limit",source="request",path="amount",
         operator="lte",expected_path="authority_context.limit",on_fail="defer",reason_code="approval_required"),
])

def attempt(request, authority, effects):
    # In a real integration, obtain fresh, authenticated authority independently.
    try:
        receipt = evaluate_action(POLICY, request, {}, authority)
        report = verify_action_decision(receipt, POLICY, request, {}, authority)
    except (ValueError, TypeError):
        return "invalid"
    if receipt.decision == "permit" and report.overall == "verified":
        effects.append(request["request_id"])  # simulated exact action, no external call
    return receipt.decision

def main():
    effects = []
    for name, amount, authority in [
        ("allowed", 10, {"active":True,"limit":20}),
        ("deferred", 30, {"active":True,"limit":20}),
        ("revoked", 10, {"active":False,"limit":20}),
        ("missing", 10, {"limit":20}),
    ]:
        print(name, attempt({"request_id":name,"action":"purchase","amount":amount},authority,effects))
    print("executed:", effects)
    assert effects == ["allowed"]

if __name__ == "__main__":
    main()
