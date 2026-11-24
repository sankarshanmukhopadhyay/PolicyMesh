import runpy
from pathlib import Path

def test_consumer_blocks_nonpermit():
    demo = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/action_governance.py"))
    attempt = demo["attempt"]
    effects = []
    for active, amount, expected in [(True,10,"permit"),(True,30,"defer"),(False,10,"deny")]:
        assert attempt({"request_id":expected,"action":"purchase","amount":amount},{"active":active,"limit":20},effects) == expected
    assert attempt({"action":"purchase"},{"active":True,"limit":20},effects) == "invalid"
    assert effects == ["permit"]


def test_consumer_blocks_failed_verification(monkeypatch):
    from types import SimpleNamespace
    demo = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/action_governance.py"))
    attempt = demo["attempt"]
    monkeypatch.setitem(attempt.__globals__, "verify_action_decision",
                        lambda *args: SimpleNamespace(overall="failed"))
    effects = []
    attempt({"request_id":"r","action":"purchase","amount":10},
            {"active":True,"limit":20}, effects)
    assert effects == []
