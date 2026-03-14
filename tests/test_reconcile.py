from links.policy_updates import build_update
from links.reconcile import reconcile


def test_reconcile_report_has_richer_fields():
    u1 = build_update('ops', {'visibility': 'village'}, actor='alice')
    u2 = build_update('ops', {'visibility': 'public'}, actor='bob', previous_policy_hash=u1.policy_hash)
    report = reconcile([u1], [u1, u2], village_id='ops')
    assert report.status == 'drift'
    assert report.remote_head == u2.policy_hash
    assert report.shared_count == 1
    assert report.missing_local == [u2.policy_hash]
