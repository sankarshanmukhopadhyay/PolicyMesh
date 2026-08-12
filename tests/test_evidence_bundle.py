from links.evidence_bundle import build_evidence_bundle, verify_evidence_bundle


def test_evidence_bundle_detects_tampering(tmp_path):
    source = tmp_path / "receipt.json"
    source.write_text('{"decision":"apply"}', encoding="utf-8")
    bundle = build_evidence_bundle(tmp_path / "evidence", event_id="evt-1", village_id="alpha", sources=[source])
    ok, errors = verify_evidence_bundle(bundle)
    assert ok and not errors
    (bundle / "receipt.json").write_text('{"decision":"reject"}', encoding="utf-8")
    ok, errors = verify_evidence_bundle(bundle)
    assert not ok
    assert any("digest mismatch" in e for e in errors)
