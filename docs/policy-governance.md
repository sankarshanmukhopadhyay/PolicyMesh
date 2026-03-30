# Policy Governance

Villages define a policy perimeter for claim acceptance and exchange. This repository supports policy updates via:

- Admin-gated API endpoint (`POST /villages/{village_id}/policy`)
- Optional signed policy update artifacts (Ed25519)

## Why signed policy updates?

Bearer tokens authenticate an operator. Signatures add:
- change provenance
- deterministic review and replay
- compatibility with offline governance workflows (PR review + artifact approval)

## Suggested operating model

- Maintain policy updates as artifacts committed to version control.
- Require signatures in higher risk deployments (`require_policy_signature=true`).
- Restrict policy signers (`policy_signer_allowlist`) to an explicit set of keys.
- Log and review all policy changes via the audit log.


## Quorum governance enhancements (v0.16.0)

This repo now supports **three policy-approval quorum models**, driven by village policy config:

1. **M-of-N (legacy)**  
   - `require_policy_signature=true`
   - `policy_signature_threshold_m=M`
   - `policy_signer_allowlist=[key_hash,...]`

2. **Weighted quorum**  
   - `policy_quorum.model="weighted"`
   - `policy_quorum.threshold_weight=...`
   - `policy_signer_weights={ key_hash: weight, ... }`

3. **Role-based quorum sets**  
   - `policy_quorum.model="role_based"`
   - `policy_quorum.role_requirements=[{"role":"core","min_signers":1},{"role":"external","min_signers":1}]`
   - `policy_signer_roles={ key_hash: ["core"], ... }`

### Quorum metadata inside update artifacts

Policy update artifacts can embed a `quorum` object (signed) so auditors can see *what quorum model and thresholds* were intended for the change.
Operators that want strictness can set `require_quorum_metadata=true` in the village policy and enforce it during review.

## Policy change lifecycle + versioning

Policy updates support lifecycle states:

- `proposal` → `approved` → `active`

And versioning/rollback metadata:

- `policy_version_id` (defaults to `policy_hash`)
- `previous_policy_hash` (links the chain)
- `rollback_to_policy_hash` (explicit rollback intent)
- `activation_time` / `activation_height` (activation semantics)

## Policy diff tooling

The CLI can compute a structured diff summary between two policy JSON files:

- `links policy diff old.json new.json`

This emits a machine-readable summary (`added`, `removed`, `changed` JSON pointer paths) that can be embedded in policy update artifacts as `change_summary`.


## Operator workflow additions

Inspect the effective quorum configuration for a village:

```bash
links policy quorum-inspect ops
```

This produces a durable JSON artifact showing the active quorum model, threshold, allowlisted signer set, signer weights, and role assignments. It is intended for operator review, troubleshooting, and audit preparation before or after a policy update is proposed.

For live federation checks, the server now exposes:

- `GET /villages/{village_id}/transparency/checkpoint`
- `GET /nodes/capability`

Together these surfaces make it possible to compare peer publication state, fetch checkpoints through a stable HTTP contract, and discover runtime capability posture without inspecting the repository by hand.
