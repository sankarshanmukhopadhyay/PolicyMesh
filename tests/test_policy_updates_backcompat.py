from links.policy_updates import build_update


def test_build_update_backward_compatible_inputs():
    u = build_update(
        'ops',
        {'visibility': 'village'},
        actor='alice',
        quorum_metadata={'model': 'm_of_n', 'threshold_m': 2},
        activation_time='2026-01-01T00:00:00Z',
        change_summary={'added': ['/foo'], 'removed': [], 'changed': []},
    )
    assert u.quorum is not None
    assert u.quorum_metadata is not None
    assert u.activation_time is not None
    assert u.change_summary is not None
    assert u.change_summary.added == ['/foo']
