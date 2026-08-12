from links.policy_updates import build_update
from links.policy_lifecycle import validate_transition, transition_update


def test_lifecycle_happy_path_and_signature_reset():
    u = build_update("alpha", {"visibility": "village"})
    approved, ev = transition_update(u, "approved", actor="admin")
    assert approved.lifecycle_state == "approved"
    assert ev.from_state == "proposal"
    assert ev.to_state == "approved"
    active, _ = transition_update(approved, "active")
    assert active.lifecycle_state == "active"


def test_invalid_transition_rejected():
    ok, msg = validate_transition("proposal", "active")
    assert not ok
    assert "invalid lifecycle transition" in msg


def test_rollback_requires_target():
    u = build_update("alpha", {"visibility": "village"}, lifecycle_state="active")
    try:
        transition_update(u, "rolled_back")
        assert False
    except ValueError as exc:
        assert "rollback requires" in str(exc)
