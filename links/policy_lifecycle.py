from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

from pydantic import BaseModel, Field

from .policy_updates import VillagePolicyUpdate, compute_policy_hash

LIFECYCLE_STATES = ("proposal", "approved", "active", "rolled_back")
_ALLOWED_TRANSITIONS = {
    "proposal": {"approved"},
    "approved": {"active"},
    "active": {"rolled_back"},
    "rolled_back": set(),
}


class PolicyLifecycleEvent(BaseModel):
    format: str = "links.policy.lifecycle.v1"
    village_id: str
    policy_hash: str
    policy_version_id: Optional[str] = None
    from_state: str
    to_state: str
    actor: Optional[str] = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: Optional[str] = None
    rollback_to_policy_hash: Optional[str] = None


def validate_transition(from_state: str, to_state: str) -> Tuple[bool, str]:
    if from_state not in LIFECYCLE_STATES or to_state not in LIFECYCLE_STATES:
        return False, "unknown lifecycle state"
    if to_state in _ALLOWED_TRANSITIONS[from_state]:
        return True, "ok"
    return False, f"invalid lifecycle transition: {from_state} -> {to_state}"


def transition_update(
    update: VillagePolicyUpdate,
    to_state: str,
    *,
    actor: Optional[str] = None,
    reason: Optional[str] = None,
    activation_time: Optional[datetime] = None,
    activation_height: Optional[int] = None,
    rollback_to_policy_hash: Optional[str] = None,
) -> Tuple[VillagePolicyUpdate, PolicyLifecycleEvent]:
    ok, msg = validate_transition(update.lifecycle_state, to_state)
    if not ok:
        raise ValueError(msg)
    if to_state == "rolled_back" and not rollback_to_policy_hash:
        raise ValueError("rollback requires rollback_to_policy_hash")
    changed = update.model_copy(update={
        "lifecycle_state": to_state,
        "actor": actor or update.actor,
        "activation_time": activation_time if activation_time is not None else update.activation_time,
        "activation_height": activation_height if activation_height is not None else update.activation_height,
        "rollback_to_policy_hash": rollback_to_policy_hash if to_state == "rolled_back" else update.rollback_to_policy_hash,
        # lifecycle mutation invalidates old signatures
        "public_key": None,
        "signature": None,
        "signatures": [],
    })
    event = PolicyLifecycleEvent(
        village_id=update.village_id,
        policy_hash=update.policy_hash,
        policy_version_id=update.policy_version_id,
        from_state=update.lifecycle_state,
        to_state=to_state,
        actor=actor,
        reason=reason,
        rollback_to_policy_hash=rollback_to_policy_hash,
    )
    return changed, event


def write_lifecycle_event(root: Path, event: PolicyLifecycleEvent) -> Path:
    out_dir = root / "artifacts" / "policy_lifecycle" / event.village_id
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = event.occurred_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"{stamp}.{event.from_state}-to-{event.to_state}.{event.policy_hash[:12]}.json"
    path.write_text(event.model_dump_json(indent=2), encoding="utf-8")
    return path


def find_policy_in_history(history_rows: List[dict], policy_hash: str) -> Optional[dict]:
    for row in reversed(history_rows):
        policy = row.get("policy") if isinstance(row, dict) else None
        if isinstance(policy, dict) and compute_policy_hash(policy) == policy_hash:
            return policy
    return None
