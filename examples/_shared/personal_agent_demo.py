from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from links.action_decisions import ActionPolicy, evaluate_action, load_json, verify_action_receipt, write_action_receipt


def run_example(example: Path, title: str, scenario: str) -> int:
    expected = load_json(example / "expected" / f"{scenario}.json")
    request = load_json(example / "requests" / f"{scenario}.json")
    evidence = load_json(example / "evidence" / expected.get("evidence", "base.json"))
    authority = load_json(example / "authority" / expected.get("authority", "active-mandate.json"))
    policy = ActionPolicy.model_validate(load_json(example / "policy" / expected["policy"]))
    receipt = evaluate_action(policy, request, evidence, authority)
    receipt_out = example / "artifacts" / f"{scenario}.receipt.json"
    write_action_receipt(receipt_out, receipt)

    print(f"PolicyMesh — {title}")
    print(f"Scenario: {scenario}")
    print(f"Action: {request['action']}")
    for result in receipt.evaluations:
        marker = "PASS" if result.result == "pass" else "FAIL"
        print(f"  {marker:4}  {result.rule_id}: {result.description}")
    print(f"DECISION: {receipt.decision.upper()}")
    print("REASONS: " + ", ".join(receipt.reason_codes))
    print(f"Receipt: {receipt_out.relative_to(ROOT)}")
    ok = receipt.decision == expected["decision"] and verify_action_receipt(receipt)
    print(f"Receipt integrity: {'OK' if verify_action_receipt(receipt) else 'FAIL'}")
    print(f"Expected: {expected['decision'].upper()} — {'MATCH' if ok else 'MISMATCH'}")
    return 0 if ok else 1


def scenario_names(example: Path):
    return sorted(p.stem for p in (example / "requests").glob("*.json"))
