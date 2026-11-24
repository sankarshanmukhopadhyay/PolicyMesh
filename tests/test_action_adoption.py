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
