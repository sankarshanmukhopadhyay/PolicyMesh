from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .file_lock import locked_open
from .storage_backend import sqlite_enabled, transaction, write_audit_event


def iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class AuditEvent:
    action: str
    bundle_id: Optional[str] = None
    village_id: Optional[str] = None
    issuer_key_hash: Optional[str] = None
    actor: Optional[str] = None
    reason: Optional[str] = None
    policy_hash: Optional[str] = None


def policy_hash(policy_obj: dict) -> str:
    import hashlib, json as _json
    b = _json.dumps(policy_obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).hexdigest()[:16]


def write_audit(store_root: Path, ev: AuditEvent) -> None:
    (store_root / "audit").mkdir(parents=True, exist_ok=True)
    p = store_root / "audit" / "audit.log.jsonl"
    row = {
        "ts": iso_utc(utc_now()),
        "action": ev.action,
        "bundle_id": ev.bundle_id,
        "village_id": ev.village_id,
        "issuer_key_hash": ev.issuer_key_hash,
        "actor": ev.actor,
        "reason": ev.reason,
        "policy_hash": ev.policy_hash,
    }
    with locked_open(p, "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if sqlite_enabled():
        with transaction(store_root) as conn:
            write_audit_event(conn, row)
