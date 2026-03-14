from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional


DEFAULT_SQLITE_PATH = Path("data/store/links.sqlite3")


def configured_backend() -> str:
    return os.environ.get("LINKS_STORAGE_BACKEND", "filesystem").strip().lower() or "filesystem"


def sqlite_path(store_root: Path = Path("data/store")) -> Path:
    raw = os.environ.get("LINKS_SQLITE_PATH", "").strip()
    if raw:
        return Path(raw)
    return store_root / DEFAULT_SQLITE_PATH.name


def sqlite_enabled() -> bool:
    return configured_backend() == "sqlite"


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS bundle_store (
            bundle_id TEXT PRIMARY KEY,
            village_id TEXT,
            issuer TEXT,
            created_at TEXT,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS claims_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bundle_id TEXT NOT NULL,
            issuer TEXT,
            village_id TEXT,
            subject TEXT,
            predicate TEXT,
            object TEXT,
            confidence REAL,
            computed_at TEXT,
            row_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            action TEXT NOT NULL,
            bundle_id TEXT,
            village_id TEXT,
            issuer_key_hash TEXT,
            actor TEXT,
            reason TEXT,
            policy_hash TEXT,
            row_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transparency_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            village_id TEXT NOT NULL,
            policy_hash TEXT NOT NULL,
            update_hash TEXT,
            entry_hash TEXT NOT NULL,
            row_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS policy_state (
            village_id TEXT PRIMARY KEY,
            policy_hash TEXT NOT NULL,
            policy_json TEXT NOT NULL,
            actor TEXT,
            applied_at TEXT NOT NULL,
            update_hash TEXT
        );
        CREATE TABLE IF NOT EXISTS policy_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_id TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            policy_hash TEXT NOT NULL,
            policy_json TEXT NOT NULL,
            update_hash TEXT,
            actor TEXT,
            row_json TEXT NOT NULL
        );
        """
    )
    conn.commit()


@contextmanager
def transaction(store_root: Path = Path("data/store")) -> Iterator[sqlite3.Connection]:
    conn = _connect(sqlite_path(store_root))
    try:
        conn.execute("BEGIN")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def write_bundle_and_claims(conn: sqlite3.Connection, bundle_id: str, village_id: Optional[str], issuer: str, created_at: str, payload_json: str, claim_rows: Iterable[Dict[str, Any]]) -> None:
    conn.execute(
        "INSERT INTO bundle_store(bundle_id, village_id, issuer, created_at, payload_json) VALUES(?,?,?,?,?)",
        (bundle_id, village_id, issuer, created_at, payload_json),
    )
    for row in claim_rows:
        conn.execute(
            "INSERT INTO claims_index(bundle_id, issuer, village_id, subject, predicate, object, confidence, computed_at, row_json) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                row.get("bundle_id"),
                row.get("issuer"),
                row.get("village_id"),
                row.get("subject"),
                row.get("predicate"),
                row.get("object"),
                row.get("confidence"),
                row.get("computed_at"),
                json.dumps(row, ensure_ascii=False, sort_keys=True),
            ),
        )


def query_claim_rows(store_root: Path = Path("data/store"), *, subject: Optional[str] = None, issuer: Optional[str] = None, predicate: Optional[str] = None, village_id: Optional[str] = None) -> list[Dict[str, Any]]:
    conn = _connect(sqlite_path(store_root))
    try:
        q = "SELECT row_json FROM claims_index WHERE 1=1"
        params: list[Any] = []
        if subject:
            q += " AND subject = ?"
            params.append(subject)
        if issuer:
            q += " AND issuer = ?"
            params.append(issuer)
        if predicate:
            q += " AND predicate = ?"
            params.append(predicate)
        if village_id:
            q += " AND village_id = ?"
            params.append(village_id)
        q += " ORDER BY id ASC"
        rows = conn.execute(q, params).fetchall()
        return [json.loads(r[0]) for r in rows]
    finally:
        conn.close()


def write_audit_event(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    conn.execute(
        "INSERT INTO audit_log(ts, action, bundle_id, village_id, issuer_key_hash, actor, reason, policy_hash, row_json) VALUES(?,?,?,?,?,?,?,?,?)",
        (
            row.get("ts"),
            row.get("action"),
            row.get("bundle_id"),
            row.get("village_id"),
            row.get("issuer_key_hash"),
            row.get("actor"),
            row.get("reason"),
            row.get("policy_hash"),
            json.dumps(row, ensure_ascii=False, sort_keys=True),
        ),
    )


def write_transparency_entry(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    conn.execute(
        "INSERT INTO transparency_log(ts, village_id, policy_hash, update_hash, entry_hash, row_json) VALUES(?,?,?,?,?,?)",
        (
            row.get("ts"),
            row.get("village_id"),
            row.get("policy_hash"),
            row.get("update_hash"),
            row.get("entry_hash"),
            json.dumps(row, ensure_ascii=False, sort_keys=True),
        ),
    )


def write_policy_apply_event(conn: sqlite3.Connection, *, village_id: str, applied_at: str, policy_hash: str, policy_obj: Dict[str, Any], actor: Optional[str], update_hash: Optional[str], history_row: Dict[str, Any]) -> None:
    policy_json = json.dumps(policy_obj, ensure_ascii=False, sort_keys=True)
    conn.execute(
        "INSERT INTO policy_state(village_id, policy_hash, policy_json, actor, applied_at, update_hash) VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(village_id) DO UPDATE SET policy_hash=excluded.policy_hash, policy_json=excluded.policy_json, actor=excluded.actor, applied_at=excluded.applied_at, update_hash=excluded.update_hash",
        (village_id, policy_hash, policy_json, actor, applied_at, update_hash),
    )
    conn.execute(
        "INSERT INTO policy_history(village_id, applied_at, policy_hash, policy_json, update_hash, actor, row_json) VALUES(?,?,?,?,?,?,?)",
        (village_id, applied_at, policy_hash, policy_json, update_hash, actor, json.dumps(history_row, ensure_ascii=False, sort_keys=True)),
    )


def fetch_policy_state(store_root: Path, village_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect(sqlite_path(store_root))
    try:
        row = conn.execute("SELECT policy_hash, policy_json, actor, applied_at, update_hash FROM policy_state WHERE village_id = ?", (village_id,)).fetchone()
        if row is None:
            return None
        return {
            "policy_hash": row[0],
            "policy": json.loads(row[1]),
            "actor": row[2],
            "applied_at": row[3],
            "update_hash": row[4],
        }
    finally:
        conn.close()
