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


def reconcile(local: List[VillagePolicyUpdate], remote: List[VillagePolicyUpdate], village_id: str) -> ReconciliationReport:
    local_set = {u.policy_hash for u in local}
    remote_set = {u.policy_hash for u in remote}

    local_head = _head(local)
    remote_head = _head(remote)
    selected_head = remote_head or local_head

    forks = detect_forks(local + remote)
    shared = local_set & remote_set
    drift = local_head != remote_head
    if forks:
        status = 'fork'
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
    )


def write_reconciliation_report(report: ReconciliationReport, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_path
