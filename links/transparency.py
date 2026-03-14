from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from nacl.signing import SigningKey

from .file_lock import locked_open
from .policy_updates import canonical_json, sha256_hex
from .storage_backend import sqlite_enabled, transaction, write_transparency_entry


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def transparency_log_path(store_root: Path, village_id: str) -> Path:
    p = store_root / "transparency" / village_id / "policy_log.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def append_transparency_entry(
    store_root: Path,
    village_id: str,
    policy_hash: str,
    update_hash: Optional[str],
    signing_key: SigningKey,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "ts": utc_now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "village_id": village_id,
        "policy_hash": policy_hash,
        "update_hash": update_hash,
        "meta": meta or {},
    }
    payload = canonical_json(entry)
    entry["entry_hash"] = sha256_hex(payload)
    entry["signature"] = signing_key.sign(payload).signature.hex()
    with locked_open(transparency_log_path(store_root, village_id), "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    if sqlite_enabled():
        with transaction(store_root) as conn:
            write_transparency_entry(conn, entry)
    return entry


def build_transparency_checkpoint(store_root: Path, village_id: str) -> Dict[str, Any]:
    p = transparency_log_path(store_root, village_id)
    entries = []
    if p.exists():
        with locked_open(p, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
    entry_hashes = [e.get("entry_hash") for e in entries if e.get("entry_hash")]
    checkpoint_hash = sha256_hex(canonical_json(entry_hashes)) if entry_hashes else sha256_hex(b"")
    latest = entries[-1] if entries else None
    return {
        "village_id": village_id,
        "generated_at": utc_now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "entry_count": len(entries),
        "checkpoint_hash": checkpoint_hash,
        "latest_entry_hash": latest.get("entry_hash") if latest else None,
        "latest_policy_hash": latest.get("policy_hash") if latest else None,
    }


def write_transparency_checkpoint(store_root: Path, village_id: str, out_path: Path) -> Path:
    payload = build_transparency_checkpoint(store_root, village_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return out_path
