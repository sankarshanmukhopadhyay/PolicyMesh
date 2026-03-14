from pathlib import Path

from nacl.signing import SigningKey

from links.transparency import append_transparency_entry, build_transparency_checkpoint


def test_transparency_checkpoint_has_stable_shape(tmp_path):
    sk = SigningKey.generate()
    append_transparency_entry(tmp_path, "ops", "hash1", "upd1", sk)
    append_transparency_entry(tmp_path, "ops", "hash2", "upd2", sk)
    checkpoint = build_transparency_checkpoint(tmp_path, "ops")
    assert checkpoint["village_id"] == "ops"
    assert checkpoint["entry_count"] == 2
    assert checkpoint["latest_policy_hash"] == "hash2"
    assert checkpoint["checkpoint_hash"]
