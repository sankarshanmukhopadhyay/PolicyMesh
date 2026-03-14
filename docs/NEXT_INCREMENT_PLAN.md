# Next Increment Plan — Federation Scale-Out and Assurance Hardening

The prior increment delivered reconciliation hardening, optional SQLite-backed durability, transparency checkpoints, and operator runbooks.

## Objective

Extend Links from a solid small-pilot governance substrate toward a more scalable and more legible federation posture.

---

## Priority 1: Signed feed trust policy

### Target outcomes
- Allow operators to pin trusted manifest signers by policy.
- Fail closed in production mode when manifests are unsigned or signed by unknown keys.
- Document bootstrap and rotation procedures for manifest trust.

---

## Priority 2: Replay-safe history traversal

### Target outcomes
- Strengthen pull replay handling across deeper histories.
- Add clearer parent-chain retrieval guidance for lineage gaps.
- Add stress tests for paginated and partial-history pulls.

---

## Priority 3: Transparency publication patterns

### Target outcomes
- Publish checkpoint artifacts over HTTP for peer comparison.
- Add digest signing for checkpoint payloads.
- Document operator workflows for exchanging checkpoints across nodes.

---

## Priority 4: Assurance and conformance surfacing

### Target outcomes
- Add machine-readable capability declarations for storage mode, reconciliation mode, and transparency features.
- Expand docs to cleanly separate production-supported from experimental features.
- Add operator-facing acceptance criteria for small-federation pilots.

---

## Explicit non-goals for this increment

- broad SDK expansion
- unrelated schema churn
- speculative standards work without operational payoff
- large architectural rewrites disconnected from operator adoption
