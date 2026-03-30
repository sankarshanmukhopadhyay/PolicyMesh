from __future__ import annotations

import base64
from pathlib import Path

from fastapi.testclient import TestClient
from nacl.signing import SigningKey

from links.server import create_app
from links.transparency import append_transparency_entry


def test_transparency_checkpoint_endpoint_returns_live_checkpoint(tmp_path):
    store_root = tmp_path / "store"
    villages_root = tmp_path / "data"
    app = create_app(store_root=store_root, villages_root=villages_root)
    client = TestClient(app)

    sk = SigningKey.generate()
    append_transparency_entry(store_root, "ops", "policy-1", "update-1", sk)

    r = client.get("/villages/ops/transparency/checkpoint")
    assert r.status_code == 200
    payload = r.json()
    assert payload["village_id"] == "ops"
    assert payload["entry_count"] == 1
    assert payload["latest_policy_hash"] == "policy-1"


def test_transparency_checkpoint_endpoint_signs_when_node_key_present(tmp_path, monkeypatch):
    store_root = tmp_path / "store"
    villages_root = tmp_path / "data"
    app = create_app(store_root=store_root, villages_root=villages_root)
    client = TestClient(app)

    sk = SigningKey.generate()
    seed_b64 = base64.b64encode(sk.encode()).decode("utf-8")
    monkeypatch.setenv("LINKS_NODE_SIGNING_KEY_B64", seed_b64)

    append_transparency_entry(store_root, "ops", "policy-1", "update-1", SigningKey.generate())

    r = client.get("/villages/ops/transparency/checkpoint")
    assert r.status_code == 200
    payload = r.json()
    assert "signature" in payload
    assert "signer_key_hash" in payload


def test_node_capability_endpoint_reflects_runtime_configuration(monkeypatch):
    monkeypatch.setenv("LINKS_NODE_ID", "node.example.org")
    monkeypatch.setenv("LINKS_STORAGE_BACKEND", "sqlite")
    monkeypatch.setenv("LINKS_RECONCILIATION_MODE", "lineage_aware")
    monkeypatch.setenv("LINKS_FEDERATION_PILOT", "true")

    sk = SigningKey.generate()
    seed_b64 = base64.b64encode(sk.encode()).decode("utf-8")
    monkeypatch.setenv("LINKS_NODE_SIGNING_KEY_B64", seed_b64)

    app = create_app(store_root=Path("data/store"), villages_root=Path("data"))
    client = TestClient(app)

    r = client.get("/nodes/capability")
    assert r.status_code == 200
    payload = r.json()
    assert payload["node_id"] == "node.example.org"
    assert payload["storage_mode"] == "sqlite"
    assert payload["reconciliation_mode"] == "lineage_aware"
    assert payload["federation_pilot"] is True
    assert "http_publish" in payload["transparency_features"]
    assert "signed_checkpoint" in payload["transparency_features"]
    assert "capability_manifest" in payload["experimental_features"]
    assert payload["extensions"]["service_version"] == "0.16.0"
