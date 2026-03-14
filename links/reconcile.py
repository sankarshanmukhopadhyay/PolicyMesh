from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import timezone
from pathlib import Path
from typing import List, Dict, Optional, Any
import json

from .policy_updates import VillagePolicyUpdate, compute_update_hash


@dataclass
class ReconciliationReport:
    village_id: str
    local_head: Optional[str]
    remote_head: Optional[str]
    selected_head: Optional[str]
    drift: bool
    status: str
    local_count: int
    remote_count: int
    shared_count: int
    fork_count: int
    forks: List[Dict[str, Any]]
    missing_local: List[str]
    missing_remote: List[str]
    generated_at: str
    selected_source: Optional[str]
    selection_reason: Optional[str]
    lineage_issues: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _head(ups: List[VillagePolicyUpdate]) -> Optional[str]:
    return max(ups, key=lambda u: (u.created_at, u.policy_hash)).policy_hash if ups else None


def detect_forks(ups: List[VillagePolicyUpdate]) -> List[Dict[str, Any]]:
    by_prev: Dict[Optional[str], List[VillagePolicyUpdate]] = {}
    for u in ups:
        by_prev.setdefault(u.previous_policy_hash, []).append(u)

    forks: List[Dict[str, Any]] = []
    for prev, children in by_prev.items():
        if prev is None:
            continue
        uniq = {c.policy_hash for c in children}
        if len(uniq) > 1:
            forks.append({
                'previous_policy_hash': prev,
                'children': sorted([
                    {
                        'policy_hash': c.policy_hash,
                        'created_at': c.created_at.isoformat(),
                        'update_hash': compute_update_hash(c),
                        'lifecycle_state': c.lifecycle_state,
                    } for c in children
                ], key=lambda x: (x['created_at'], x['policy_hash'])),
            })
    return forks


def _lineage_issues(ups: List[VillagePolicyUpdate]) -> List[Dict[str, Any]]:
    seen = {u.policy_hash for u in ups}
    issues: List[Dict[str, Any]] = []
    for u in ups:
        prev = u.previous_policy_hash
        if prev and prev not in seen:
            issues.append({
                "policy_hash": u.policy_hash,
                "previous_policy_hash": prev,
                "issue": "missing_parent",
            })
    return issues


def reconcile(local: List[VillagePolicyUpdate], remote: List[VillagePolicyUpdate], village_id: str) -> ReconciliationReport:
    local_set = {u.policy_hash for u in local}
    remote_set = {u.policy_hash for u in remote}

    local_head = _head(local)
    remote_head = _head(remote)

    forks = detect_forks(local + remote)
    shared = local_set & remote_set
    lineage_issues = _lineage_issues(local + remote)
    drift = local_head != remote_head

    if remote_head and remote_head in local_set:
        selected_head = remote_head
        selected_source = "shared"
        selection_reason = "remote head already present locally"
    elif remote_head and not forks and not lineage_issues:
        selected_head = remote_head
        selected_source = "remote"
        selection_reason = "remote head is newer and lineage is consistent"
    else:
        selected_head = local_head or remote_head
        selected_source = "local" if local_head else ("remote" if remote_head else None)
        if forks:
            selection_reason = "retained local head because reconciliation detected a fork"
        elif lineage_issues:
            selection_reason = "retained local head because update lineage is incomplete"
        else:
            selection_reason = "retained local head as deterministic fallback"

    if forks:
        status = 'fork'
    elif lineage_issues:
        status = 'lineage_gap'
    elif drift:
        status = 'drift'
    else:
        status = 'aligned'

    return ReconciliationReport(
        village_id=village_id,
        local_head=local_head,
        remote_head=remote_head,
        selected_head=selected_head,
        drift=drift,
        status=status,
        local_count=len(local_set),
        remote_count=len(remote_set),
        shared_count=len(shared),
        fork_count=len(forks),
        forks=forks,
        missing_local=sorted(list(remote_set - local_set)),
        missing_remote=sorted(list(local_set - remote_set)),
        generated_at=__import__('datetime').datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        selected_source=selected_source,
        selection_reason=selection_reason,
        lineage_issues=lineage_issues,
    )


def write_reconciliation_report(report: ReconciliationReport, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_path
