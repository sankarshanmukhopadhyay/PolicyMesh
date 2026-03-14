from datetime import datetime, timezone

from nacl.signing import SigningKey

from links.claims import Claim, ClaimBundle, sign_bundle, compute_bundle_id, bundle_payload_for_signing
from links.store import ingest_bundle_file, query_claims
from links.villages import Village, VillageGovernance, VillagePolicy, save_village, apply_policy_update
from links.storage_backend import fetch_policy_state


def test_sqlite_claim_index_and_policy_state(tmp_path, monkeypatch):
    monkeypatch.setenv("LINKS_STORAGE_BACKEND", "sqlite")
    monkeypatch.setenv("LINKS_SQLITE_PATH", str(tmp_path / "links.sqlite3"))

    store_root = tmp_path / "store"
    data_root = tmp_path / "data"
    data_root.mkdir(parents=True, exist_ok=True)

    created = datetime.now(timezone.utc)
    sk = SigningKey.generate()
    claim = Claim(
        issuer="issuer:test",
        subject="did:example:alice",
        predicate="links.weighted_to",
        object="did:example:bob",
        window_days=7,
        computed_at=created,
    )
    bundle = ClaimBundle(bundle_id="", issuer="issuer:test", created_at=created, window_days=7, claims=[claim])
    bundle = bundle.model_copy(update={"bundle_id": compute_bundle_id(bundle_payload_for_signing(bundle))})
    signed = sign_bundle(bundle, sk)
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(signed.model_dump_json(indent=2), encoding="utf-8")

    ok, _ = ingest_bundle_file(bundle_path, store_root=store_root)
    assert ok is True
    rows = query_claims(subject="did:example:alice", store_root=store_root)
    assert len(rows) == 1
    assert rows[0]["predicate"] == "links.weighted_to"

    v = Village(
        village_id="ops",
        name="Ops",
        governance=VillageGovernance(admins=["alice"]),
        policy=VillagePolicy(),
        created_at=created,
    )
    save_village(data_root, v)

    import links.villages as villages_mod
    orig = villages_mod.store_root
    villages_mod.store_root = store_root
    try:
        apply_policy_update(data_root, "ops", {"visibility": "public"}, actor="alice", update_meta={"policy_hash": "abc123", "policy_update": "test", "ts": "2026-03-14T10:00:00Z"})
    finally:
        villages_mod.store_root = orig

    state = fetch_policy_state(store_root, "ops")
    assert state is not None
    assert state["policy"]["visibility"] == "public"
