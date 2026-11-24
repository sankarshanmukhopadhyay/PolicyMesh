import runpy
from pathlib import Path
import pytest

DEMO = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/vti_local_gate.py"))
REQUEST = {"request_id":"r","action":"synthetic-operation","actor":"A","operation_digest":"mock-A"}
AUTHORITY = {"native_status":"eligible","fresh":True,"actor":"A","operation_digest":"mock-A"}
EVIDENCE = {"approved_digest":"mock-A","local_allowed":True}

@pytest.mark.parametrize("req,auth,ev,decision", [
    ({},{},{},"permit"),
    ({},{"native_status":"refused"},{},"deny"),
    ({},{"native_status":"indeterminate"},{},"deny"),
    ({},{"fresh":False},{},"deny"),
    ({"actor":"B"},{},{},"deny"),
    ({"operation_digest":"mock-B"},{},{},"deny"),
    ({},{},{"approved_digest":None},"defer"),
    ({},{},{"approved_digest":"mock-B"},"defer"),
    ({},{},{"local_allowed":False},"deny"),
], ids=["PM-VTI-001","PM-VTI-002","PM-VTI-003","PM-VTI-004","PM-VTI-005","PM-VTI-006","PM-VTI-007","PM-VTI-008","PM-VTI-009"])
def test_local_composition(req,auth,ev,decision):
    receipt, report, eligible = DEMO["assess"]({**REQUEST,**req},{**AUTHORITY,**auth},{**EVIDENCE,**ev})
    assert receipt.decision == decision
    assert report.overall == "verified"
    assert report.authority_validation == "not_checked"
    assert eligible == (decision == "permit")

def test_absent_native_authority():
    receipt, _, eligible = DEMO["assess"](REQUEST,{},EVIDENCE)
    assert receipt.decision == "deny"
    assert not eligible
