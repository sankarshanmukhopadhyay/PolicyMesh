from datetime import datetime, timezone, timedelta
import hashlib

from nacl.signing import SigningKey
from fastapi.testclient import TestClient

from links.policy_feed import (
    PolicyFeedManifest,
    fill_history_gaps,
    sign_manifest,
    store_policy_update,
    verify_manifest_against_policy,
)
from links.policy_updates import VillagePolicyUpdate, build_update, compute_policy_hash
from links.server import create_app


def test_verify_manifest_against_policy_trusted_signer():
    sk = SigningKey.generate()
    signer_hash = hashlib.sha256(sk.verify_key.encode()).hexdigest()
    manifest = PolicyFeedManifest(
        village_id="ops",
        generated_at=datetime.now(timezone.utc),
        head_policy_hash="abc",
        count=0,
        merkle_root="0" * 64,
        chain_head="0" * 64,
        items=[],
    )
    signed = sign_manifest(manifest, sk)
    policy = {
        "trusted_manifest_signer_allowlist": [signer_hash],
        "require_manifest_signature": True,
        "require_trusted_manifest_signer": True,
    }
    ok, msg = verify_manifest_against_policy(policy, signed)
    assert ok is True
    assert "trusted signer" in msg


def test_verify_manifest_against_policy_rejects_unsigned_when_required():
    manifest = PolicyFeedManifest(
        village_id="ops",
        generated_at=datetime.now(timezone.utc),
        head_policy_hash="abc",
        count=0,
        merkle_root="0" * 64,
        chain_head="0" * 64,
        items=[],
    )
    policy = {"require_manifest_signature": True}
    ok, msg = verify_manifest_against_policy(policy, manifest)
    assert ok is False
    assert "unsigned manifest rejected by policy" == msg


def test_fill_history_gaps_fetches_missing_parents():
    u1 = build_update("ops", {"visibility": "village"}, actor="alice")
    u2 = build_update("ops", {"visibility": "public"}, actor="alice", previous_policy_hash=u1.policy_hash)
    u3 = build_update("ops", {"visibility": "public", "retention_days": 120}, actor="alice", previous_policy_hash=u2.policy_hash)

    def fetch(policy_hash: str):
        lookup = {u1.policy_hash: u1, u2.policy_hash: u2, u3.policy_hash: u3}
        return lookup.get(policy_hash)

    combined, fetched, unresolved = fill_history_gaps([u3], known_policy_hashes=set(), fetch_update_by_hash=fetch)
    assert [u.policy_hash for u in combined] == [u1.policy_hash, u2.policy_hash, u3.policy_hash]
    assert fetched == [u2.policy_hash, u1.policy_hash]
    assert unresolved == []


def test_policy_update_by_hash_endpoint(tmp_path):
    root = tmp_path
    village_id = "ops"
    p1 = {"visibility": "village"}
    u1 = VillagePolicyUpdate(
        village_id=village_id,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        actor="a",
        policy=p1,
        policy_hash=compute_policy_hash(p1),
    )
    store_policy_update(root, u1)

    app = create_app(store_root=root / "store", villages_root=root)
    client = TestClient(app)
    resp = client.get(f"/villages/{village_id}/policy/by_hash/{u1.policy_hash}")
    assert resp.status_code == 200
    assert resp.json()["policy_hash"] == u1.policy_hash
