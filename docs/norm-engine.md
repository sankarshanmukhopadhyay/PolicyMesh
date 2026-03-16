# Norm Engine

PolicyMesh v0.15.0 introduces a first-class norm engine so villages can author governance intent in a structured form and compile it into executable village policy.

## Why this exists

Earlier versions assumed that policy artifacts already existed. That worked for pull/apply federation and signature verification, but it left a conceptual hole between community governance and policy transport.

The norm engine closes that gap:

1. a village declares a `NormSet`
2. the compiler maps known governance patterns into machine policy
3. the compiled artifact records provenance and source norm IDs
4. the compiled policy can be applied through the existing policy lifecycle

## What it is not

This is not a natural-language policy oracle, not a voting engine, and not a deliberation platform. v0.15.0 keeps the compiler deterministic, constrained, and inspectable.

## Primary objects

- `NormSet`: structured governance input authored by a village
- `CompiledPolicyArtifact`: machine-readable policy output with lineage
- `PolicyLineage`: provenance metadata from source norms to output policy hash

## Supported compilation patterns

- quarantine external bundles
- set minimum review approvals
- require signed policy updates
- set policy signature threshold
- require signed manifests during policy pull
- require trusted manifest signers
- enable transparency checkpoint signalling

## CLI flow

```bash
links norms init ops --out artifacts/norms/ops.norms.json
links norms validate artifacts/norms/ops.norms.json
links norms compile artifacts/norms/ops.norms.json --out artifacts/policy/ops.compiled.json
links policy apply-compiled artifacts/policy/ops.compiled.json --actor norm-compiler
```

## Design principle

Human governance is messy. Infrastructure should not pretend otherwise. The compiler therefore only maps explicit, supported norm templates into policy fields and rejects contradictions early.
