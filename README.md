# Links

Links is a small-footprint system for producing **verifiable, inspectable claim bundles** and exchanging them between nodes with **group policy controls**.

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
- Production deployment guidance: [`docs/deploy/production-hardened.md`](./docs/deploy/production-hardened.md)
- SQLite backend guidance: [`docs/deploy/sqlite-backend.md`](./docs/deploy/sqlite-backend.md)
- Operator playbook: [`docs/deploy/operator-playbook.md`](./docs/deploy/operator-playbook.md)
- Governance risk crosswalk: [`docs/risk-crosswalk.md`](./docs/risk-crosswalk.md)
- Upstream snapshot notes: [`upstream/UPSTREAM_SNAPSHOT.md`](./upstream/UPSTREAM_SNAPSHOT.md)

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

- M-of-N signer quorum for policy updates
- policy diff tooling and machine-readable change summaries
- policy version identifiers and deterministic rollback by prior policy hash
- policy feed pull/apply flow and drift detection CLI
- trust anchor register / rotate / revoke primitives

#### Partially implemented or still hardening

- weighted signer and role-based quorum models
- richer policy lifecycle semantics across proposal, approval, and activation
- signed feed manifests, large-history pagination, and multi-node reconciliation hardening
- transparency and audit signing workflows for production operations

#### Next priorities

- weighted or role-based quorum operationalization beyond the current artifact model
- larger-fleet federation workflows and richer replay handling
- stronger audit signing and transparency publication pipelines
- broader SDK stabilization and ecosystem integration work

## Operations

### TLS and exposure

Links is designed to run **behind a TLS terminator** (Nginx/Envoy/Cloud LB). The built-in server is suitable for dev and controlled environments.

- Binding to non-loopback interfaces will emit a warning in the CLI.
- Terminate TLS at the edge and forward to Links over a private network.

### Authentication tokens

If village membership/auth is enabled, use `Authorization: Bearer <token>` for management operations.

### Rate limiting

Links enforces a basic **in-memory per-village rate limit** using the village policy field `rate_limit_per_min`. For production, enforce rate limiting at the gateway as well.

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
