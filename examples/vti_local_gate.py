"""Synthetic composition example. No VTI protocol or authority verification."""
from links.sdk import ActionPolicy, evaluate_action, verify_action_decision
from links.utils import canonical_json, sha256_hex

def rule(name, source, path, expected=None, expected_path=None, on_fail="deny"):
    return dict(rule_id=name, description=name, source=source, path=path,
                operator="eq", expected=expected, expected_path=expected_path,
                on_fail=on_fail, reason_code=name)

POLICY = ActionPolicy(policy_id="synthetic-vti-gate", version="1", title="Additional local gate", rules=[
    rule("native_eligible", "authority_context", "native_status", "eligible"),
    rule("fresh", "authority_context", "fresh", True),
    rule("actor_bound", "request", "actor", expected_path="authority_context.actor"),
    rule("operation_bound", "request", "operation_digest", expected_path="authority_context.operation_digest"),
    rule("approval_bound", "request", "operation_digest", expected_path="evidence.approved_digest", on_fail="defer"),
    rule("local_allowed", "evidence", "local_allowed", True),
])

def local_operation_digest(request):
    """Bind the complete local candidate, not the canonical VTI wire payload."""
    if "operation_digest" in request:
        raise ValueError("operation_digest is derived, not caller-supplied")
    return sha256_hex(canonical_json(request))


def assess(request, authority, evidence):
    request = {**request, "operation_digest": local_operation_digest(request)}
    receipt = evaluate_action(POLICY, request, evidence, authority)
    report = verify_action_decision(receipt, POLICY, request, evidence, authority)
    # Eligibility for native execution/recheck is not execution or task completion.
    return receipt, report, receipt.decision == "permit" and report.overall == "verified"

def main():
    request = {"request_id":"demo", "action":"synthetic-operation", "actor":"delegate-A", "resource":"example-A"}
    digest = local_operation_digest(request)
    authority = {"native_status":"eligible", "fresh":True, "actor":"delegate-A", "operation_digest":digest}
    evidence = {"approved_digest":digest, "local_allowed":True}
    for label, a, e in [
        ("eligible", authority, evidence),
        ("native-refusal", {**authority,"native_status":"refused"}, evidence),
        ("stale", {**authority,"fresh":False}, evidence),
        ("unresolved-approval", authority, {"local_allowed":True}),
        ("local-refusal", authority, {**evidence,"local_allowed":False}),
    ]:
        receipt, report, eligible = assess(request,a,e)
        print(label, receipt.decision, report.overall, eligible)

if __name__ == "__main__":
    main()
