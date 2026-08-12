#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from links.action_decisions import ActionPolicy, evaluate_action, load_json, verify_action_receipt, write_action_receipt
from links.norms import compile_norm_set, validate_norm_file, write_json

EXAMPLE = Path(__file__).resolve().parent
SCENARIOS = sorted(p.stem for p in (EXAMPLE / "requests").glob("*.json"))


def run_scenario(name: str) -> int:
    expected = load_json(EXAMPLE / "expected" / f"{name}.json")
    request = load_json(EXAMPLE / "requests" / f"{name}.json")
    evidence = load_json(EXAMPLE / "evidence" / "base.json")
    authority = load_json(EXAMPLE / "authority" / expected["authority"])
    policy = ActionPolicy.model_validate(load_json(EXAMPLE / "policy" / "corporate-hotel-booking.action-policy.json"))

    # Compile the PolicyMesh node-governance norms as part of every end-to-end run.
    norm_set = validate_norm_file(EXAMPLE / "norms" / "node-governance.norms.json")
    compiled = compile_norm_set(norm_set).artifact
    compiled_out = EXAMPLE / "artifacts" / "compiled-node-policy.json"
    write_json(compiled_out, compiled)

    receipt = evaluate_action(policy, request, evidence, authority)
    receipt_out = EXAMPLE / "artifacts" / f"{name}.receipt.json"
    write_action_receipt(receipt_out, receipt)

    print("PolicyMesh — Travel & Hospitality Demo")
    print(f"Scenario: {name}")
    print(f"Request: {request['action']} at {request.get('hotel_id')}")
    print(f"Node policy hash: {compiled.policy_hash}")
    for result in receipt.evaluations:
        marker = "PASS" if result.result == "pass" else "FAIL"
        print(f"  {marker:4}  {result.rule_id}: {result.description}")
    print(f"DECISION: {receipt.decision.upper()}")
    print("REASONS: " + ", ".join(receipt.reason_codes))
    print(f"Receipt: {receipt_out.relative_to(ROOT)}")
    print(f"Receipt integrity: {'OK' if verify_action_receipt(receipt) else 'FAIL'}")

    ok = receipt.decision == expected["decision"] and verify_action_receipt(receipt)
    print(f"Expected: {expected['decision'].upper()} — {'MATCH' if ok else 'MISMATCH'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the PolicyMesh travel and hospitality reference example")
    parser.add_argument("scenario", nargs="?", default="permitted-booking", choices=SCENARIOS + ["all"])
    args = parser.parse_args()
    if args.scenario == "all":
        failures = 0
        for scenario in SCENARIOS:
            print("\n" + "=" * 72)
            failures += run_scenario(scenario)
        return 1 if failures else 0
    return run_scenario(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
