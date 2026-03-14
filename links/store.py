from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Iterable

from .claims import ClaimBundle, verify_bundle, iso_utc
from .file_lock import locked_open
from .storage_backend import sqlite_enabled, transaction, write_bundle_and_claims, query_claim_rows


def ensure_dirs(store_root: Path) -> None:
    (store_root / "bundles").mkdir(parents=True, exist_ok=True)
    (store_root / "index").mkdir(parents=True, exist_ok=True)
    (store_root / "quarantine").mkdir(parents=True, exist_ok=True)
    (store_root / "rejected").mkdir(parents=True, exist_ok=True)
    (store_root / "audit").mkdir(parents=True, exist_ok=True)


def ingest_bundle_file(bundle_path: Path, store_root: Path = Path("data/store")) -> tuple[bool, str]:
    """
    Ingest a signed bundle into the store:
      - verify signature + bundle_id
      - store bundle under bundles/[village_id]/bundle_id.json (if village_id present)
      - append flattened claim rows to index/claims.jsonl (locked)
    """
    ensure_dirs(store_root)
    bundle = ClaimBundle.model_validate_json(bundle_path.read_text(encoding="utf-8"))
    if not verify_bundle(bundle):
        return False, "bundle failed verification (signature and/or bundle_id mismatch)"

    subdir = store_root / "bundles"
    village_id = getattr(bundle, "village_id", None)
    if village_id:
        subdir = subdir / str(village_id)
        subdir.mkdir(parents=True, exist_ok=True)

    bundle_out = subdir / f"{bundle.bundle_id}.json"

    # Replay protection: reject if this bundle_id already exists in the store
    if bundle_out.exists():
        return False, "replay detected: bundle_id already ingested"
    
    # Atomic-ish write: write temp then replace
    tmp_out = bundle_out.with_suffix(".json.tmp")
    tmp_out.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
    tmp_out.replace(bundle_out)
    
    rows = []
    for c in bundle.claims:
        rows.append({
            "bundle_id": bundle.bundle_id,
            "issuer": bundle.issuer,
            "window_days": bundle.window_days,
            "created_at": iso_utc(bundle.created_at),
            "village_id": village_id,
            "visibility": getattr(bundle, "visibility", None),
            **c.model_dump(),
            "computed_at": iso_utc(c.computed_at),
        })

    idx = store_root / "index" / "claims.jsonl"
    n = 0
    with locked_open(idx, "a") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1

    if sqlite_enabled():
        with transaction(store_root) as conn:
            write_bundle_and_claims(
                conn,
                bundle_id=bundle.bundle_id,
                village_id=village_id,
                issuer=bundle.issuer,
                created_at=iso_utc(bundle.created_at),
                payload_json=bundle.model_dump_json(indent=2),
                claim_rows=rows,
            )

    return True, f"ingested bundle {bundle.bundle_id} with {n} claims"


def iter_claim_rows(store_root: Path = Path("data/store")) -> Iterable[dict]:
    if sqlite_enabled():
        return iter(query_claim_rows(store_root))
    idx = store_root / "index" / "claims.jsonl"
    if not idx.exists():
        return []
    def _gen():
        with idx.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)
    return _gen()


def query_claims(subject: Optional[str] = None, issuer: Optional[str] = None, predicate: Optional[str] = None, village_id: Optional[str] = None, store_root: Path = Path("data/store")) -> list[dict]:
    if sqlite_enabled():
        return query_claim_rows(store_root, subject=subject, issuer=issuer, predicate=predicate, village_id=village_id)
    out = []
    for row in iter_claim_rows(store_root):
        if subject and row.get("subject") != subject:
            continue
        if issuer and row.get("issuer") != issuer:
            continue
        if predicate and row.get("predicate") != predicate:
            continue
        if village_id and row.get("village_id") != village_id:
            continue
        out.append(row)
    return out
