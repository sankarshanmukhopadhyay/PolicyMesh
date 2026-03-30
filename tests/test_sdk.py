from __future__ import annotations

from nacl.signing import SigningKey

from links import sdk


def test_sdk_exports_stable_surface():
    assert sdk.__version__ == "0.16.0"
    manifest = sdk.build_manifest(node_id="node.example.org")
    ok, msg = sdk.verify_manifest_hash(manifest)
    assert ok is True
    assert msg == "ok"

    sk = SigningKey.generate()
    checkpoint = {
        "village_id": "ops",
        "generated_at": "2026-03-30T00:00:00Z",
        "entry_count": 1,
        "checkpoint_hash": "abc123",
        "latest_policy_hash": "policy-1",
    }
    signed = sdk.sign_checkpoint(checkpoint, sk)
    valid, _ = sdk.verify_checkpoint_signature(signed, sk.verify_key)
    assert valid is True
