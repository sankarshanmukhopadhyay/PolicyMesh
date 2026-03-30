# PolicyMesh

PolicyMesh is a small-footprint system for producing **verifiable, inspectable claim bundles** and exchanging them between nodes with **group policy controls**.

## What you get

- **Claim bundles**: portable JSON artifacts with explicit claims + signature integrity
- **Local store**: filesystem-backed storage of verified bundles + flattened index for querying
- **Villages**: groups with membership, access control, and policy norms for acceptance
- **Quarantine**: a review workflow for policy failures
- **Audit log**: append-only operational trace of decisions

## Project docs

- Roadmap: [`ROADMAP.md`](./ROADMAP.md)
- Next increment plan: [`docs/NEXT_INCREMENT_PLAN.md`](./docs/NEXT_INCREMENT_PLAN.md)
- Policy governance: [`docs/policy-governance.md`](./docs/policy-governance.md)
- Norm engine: [`docs/norm-engine.md`](./docs/norm-engine.md)
- Norm-to-policy mapping: [`docs/norm-to-policy.md`](./docs/norm-to-policy.md)
- Production deployment guidance: [`docs/deploy/production-hardened.md`](./docs/deploy/production-hardened.md)
- SQLite backend guidance: [`docs/deploy/sqlite-backend.md`](./docs/deploy/sqlite-backend.md)
- Operator playbook: [`docs/deploy/operator-playbook.md`](./docs/deploy/operator-playbook.md)
- Governance risk crosswalk: [`docs/risk-crosswalk.md`](./docs/risk-crosswalk.md)
- Upstream snapshot notes: [`upstream/UPSTREAM_SNAPSHOT.md`](./upstream/UPSTREAM_SNAPSHOT.md)

## Live federation surfaces and quorum operations (v0.16.0)

PolicyMesh now exposes live HTTP surfaces for transparency checkpoints and node capability discovery, adds an operator-facing quorum inspection workflow, and stabilizes the public Python SDK façade for federation and governance tooling.

### Live node surfaces

```bash
curl http://127.0.0.1:8080/nodes/capability
curl http://127.0.0.1:8080/villages/ops/transparency/checkpoint
```

The node capability endpoint returns a machine-readable capability manifest derived from runtime configuration. The transparency checkpoint endpoint returns the current village checkpoint and signs it automatically when `LINKS_NODE_SIGNING_KEY_B64` is configured.

### Quorum inspection

```bash
links policy quorum-inspect ops
```

This writes a durable artifact under `artifacts/quorum/<village_id>/...` so operators can inspect effective threshold, signer allowlist, signer weights, and role assignments before approving or troubleshooting policy updates.

### Stable SDK surface

```python
from links.sdk import build_manifest, fetch_peer_checkpoint, compare_checkpoints

manifest = build_manifest(node_id="node.example.org")
peer = fetch_peer_checkpoint("https://peer.example.org", "ops")
report = compare_checkpoints(local_checkpoint, peer)
```

The `links.sdk` module is the stable import surface for capability manifests, checkpoint exchange, and the minimal HTTP client.

## Norm compilation and governance authoring (v0.15.0)

PolicyMesh now includes a first-class norm engine so villages can declare structured governance intent and compile it into executable policy artifacts with provenance.

### Norm authoring

```bash
links norms init ops --out artifacts/norms/ops.norms.json
links norms validate artifacts/norms/ops.norms.json
links norms compile artifacts/norms/ops.norms.json --out artifacts/policy/ops.compiled.json
links policy apply-compiled artifacts/policy/ops.compiled.json --actor norm-compiler
```

The compiled artifact preserves source norm set ID, source norm IDs, compiler version, and output policy hash.

## Transparency and federation (v0.14.0)

### Capability manifest

```python
from links.capability_manifest import build_manifest, write_manifest
from pathlib import Path

manifest = build_manifest(
    node_id="node.example.org",
    storage_mode="sqlite",
    reconciliation_mode="lineage_aware",
    transparency_features=["http_publish", "signed_checkpoint"],
    federation_pilot=True,
)
write_manifest(Path("artifacts/capability_manifest.json"), manifest)
```

### Checkpoint signing and peer comparison

```python
from nacl.signing import SigningKey
from links.checkpoint_exchange import sign_checkpoint, fetch_peer_checkpoint, compare_checkpoints

sk = SigningKey.generate()
signed = sign_checkpoint(local_checkpoint, sk)

peer = fetch_peer_checkpoint("https://peer.example.org", "ops")
report = compare_checkpoints(signed, peer)
print(report.drift_class)   # "aligned" | "publication_lag" | "policy_divergence" | ...
print(report.notes)
```

### Drift class taxonomy

```python
from links.drift_classes import classify_checkpoint_drift, DRIFT_CLASS_OPERATOR_RESPONSE

drift_class, notes = classify_checkpoint_drift(
    local_policy_hash=local_hash,
    peer_policy_hash=peer_hash,
    local_entry_count=local_count,
    peer_entry_count=peer_count,
)
print(DRIFT_CLASS_OPERATOR_RESPONSE[drift_class])
```

## Install

```bash
pip install -e .
```

Optional durable local backend:

```bash
export LINKS_STORAGE_BACKEND=sqlite
export LINKS_SQLITE_PATH=data/store/links.sqlite3
```

## Run a node

```bash
links serve --host 127.0.0.1 --port 8080
```

### TLS and deployment posture

Bearer tokens are credentials. For any non-local deployment, run this service **behind TLS** (reverse proxy / ingress) and treat logs as sensitive.

## Villages

Create a village:

```bash
links villages create ops "Ops Village" alice
```

The command prints an **admin bearer token once**. Store it securely.

Push to a village inbox:

```bash
links sync push-village http://127.0.0.1:8080 ops <TOKEN> --bundle artifacts/claims/claim_bundle.signed.json
```

Pull the latest village bundle:

```bash
links sync pull-village http://127.0.0.1:8080 ops <TOKEN>
```

## Quarantine review

```bash
links quarantine list --village-id ops
links quarantine approve data/store/quarantine/ops/<BUNDLE_ID>.json
links quarantine reject data/store/quarantine/ops/<BUNDLE_ID>.json --reason "policy mismatch"
```

Approvals re-check current village policy before ingestion.

## Documentation

- [`docs/ethics.md`](./docs/ethics.md)
- [`docs/risks.md`](./docs/risks.md)
- [`docs/risk-crosswalk.md`](./docs/risk-crosswalk.md)

## Policy feed and reconciliation

Nodes can publish village policy updates and other nodes can **pull**, verify, reconcile, and apply them.

### Policy feed endpoints

- `GET /villages/{village_id}/policy/latest`
- `GET /villages/{village_id}/policy/updates?since=<policy_hash>`
- `POST /villages/{village_id}/policy` (stores an update; may be admin-gated depending on local village configuration)

### Pull + apply (client)

```bash
links policy pull http://127.0.0.1:8080 ops --apply
```

### Drift detection

```bash
links policy drift http://127.0.0.1:8080 ops
python scripts/policy_drift_check.py http://127.0.0.1:8080 ops
```

Reconciliation rule: prefer a consistent remote head only when lineage is intact; otherwise retain the local head as a deterministic fallback. Durable reports can be written under `artifacts/reconciliation/<village_id>/...`.

### M-of-N signer quorum for policy updates

Villages can require a signer quorum for policy updates:

- `require_policy_signature: true`
- `policy_signature_threshold_m: <M>`
- `policy_signer_allowlist: [<key-hash-1>, <key-hash-2>, ...]`

A policy update is accepted only if at least **M distinct allowlisted signers** have produced valid signatures over the update payload.

#### Creating a multisig policy update artifact

Generate an unsigned update, then have multiple operators append signatures:

```bash
# signer A
links policy sign-add artifacts/policy_update.json keys/policy/alice.key artifacts/policy_update.s1.json

# signer B (appends on top)
links policy sign-add artifacts/policy_update.s1.json keys/policy/bob.key artifacts/policy_update.s2.json
```

Verify:

```bash
links policy verify artifacts/policy_update.s2.json
```

### Governance capability status

#### Implemented governance capabilities

- structured norm authoring with deterministic norm compilation
- compiled policy provenance and source norm lineage
- CLI support for norm init, validate, compile, and diff
- compiled-policy apply workflow feeding the existing policy lifecycle
- M-of-N signer quorum for policy updates
- policy diff tooling and machine-readable change summaries
- policy version identifiers and deterministic rollback by prior policy hash
- policy feed pull/apply flow and drift detection CLI
- trust anchor register / rotate / revoke primitives

#### Delivered in v0.16.0

- live HTTP transparency checkpoint endpoint for peer fetch and comparison
- live node capability manifest endpoint for peer discovery and operator inspection
- quorum inspection CLI with durable artifacts under `artifacts/quorum/`
- stable `links.sdk` façade for capability and federation workflows

#### Still hardening

- richer policy lifecycle semantics across proposal, approval, and activation
- signed feed manifests with policy-pinned trust evaluation and deep-history parent-chain recovery
- stricter quorum metadata enforcement policies and broader operator examples
- transparency and audit signing workflows for production operations

#### Delivered in v0.15.0

- first-class norm engine and compiled policy artifact model (`links.norms`)
- deterministic norm compiler with contradiction checks and provenance
- new schemas for norm sets and compiled policy artifacts
- operator docs and examples for governance authoring

#### Previously delivered in v0.14.0

- transparency checkpoint signing, publication, and peer comparison (`links.checkpoint_exchange`)
- drift class taxonomy distinguishing policy divergence from publication lag (`links.drift_classes`)
- machine-readable capability declarations with compatibility checks (`links.capability_manifest`)
- JSON Schema for capability manifests (`schemas/capability_manifest.schema.json`)
- operator acceptance criteria for small-federation pilots

#### Next priorities

- weighted or role-based quorum operationalization beyond the current artifact model
- live HTTP endpoint for capability manifest and checkpoint serving
- broader SDK stabilization and ecosystem integration work

## Operations

### TLS and exposure

PolicyMesh is designed to run **behind a TLS terminator** (Nginx/Envoy/Cloud LB). The built-in server is suitable for dev and controlled environments.

- Binding to non-loopback interfaces will emit a warning in the CLI.
- Terminate TLS at the edge and forward to PolicyMesh over a private network.

### Authentication tokens

If village membership/auth is enabled, use `Authorization: Bearer <token>` for management operations.

### Rate limiting

PolicyMesh enforces a basic **in-memory per-village rate limit** using the village policy field `rate_limit_per_min`. For production, enforce rate limiting at the gateway as well.

### Quarantine workflow

Quarantine approvals **re-check the current village policy** before ingestion. If the policy no longer allows the bundle (predicate/window/issuer constraints), the bundle remains quarantined.


### Reconciliation CLI

```bash
links policy reconcile local_updates.json remote_updates.json ops
```

The command emits a richer reconciliation report and writes a durable JSON artifact under `artifacts/reconciliation/`.

### GitHub Pages

This repository includes GitHub Actions workflows for test execution and Pages deployment. See [`docs/deploy/pages.md`](./docs/deploy/pages.md).

### Transparency checkpoints

```bash
links drift checkpoint ops
python scripts/transparency_checkpoint.py ops
```

These write durable checkpoint artifacts under `artifacts/transparency/<village_id>/...` for operator comparison and incident review.
