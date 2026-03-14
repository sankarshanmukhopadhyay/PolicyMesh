from links.policy_updates import build_update
from links.reconcile import reconcile


def test_reconcile_prefers_local_on_lineage_gap():
    local = [build_update('ops', {'visibility': 'village'}, actor='alice')]
    remote = [build_update('ops', {'visibility': 'public'}, actor='bob', previous_policy_hash='missing-parent')]
    report = reconcile(local, remote, village_id='ops')
    assert report.status == 'lineage_gap'
    assert report.selected_source == 'local'
    assert report.lineage_issues
