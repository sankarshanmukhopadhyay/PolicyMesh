# Next Increment Plan — Transparency Exchange and Capability Surfacing

The prior increment delivered policy-pinned manifest trust, fail-closed pull controls, replay-safe parent-chain retrieval, and deeper pull-path tests.

## Objective

Extend Links from a federation-capable pull substrate toward a more legible and more exchangeable operator posture.

---

## Priority 1: Transparency publication patterns

### Target outcomes
- Publish checkpoint artifacts over HTTP for peer comparison.
- Add digest signing for checkpoint payloads.
- Document operator workflows for exchanging checkpoints across nodes.

---

## Priority 2: Assurance and conformance surfacing

### Target outcomes
- Add machine-readable capability declarations for storage mode, reconciliation mode, and transparency features.
- Expand docs to cleanly separate production-supported from experimental features.
- Add operator-facing acceptance criteria for small-federation pilots.

---

## Priority 3: Federation comparison workflows

### Target outcomes
- Add peer-to-peer checkpoint comparison tooling.
- Surface drift classes that distinguish policy divergence from publication lag.
- Add operator guidance for recovery after asymmetric history availability.

---

## Explicit non-goals for this increment

- broad SDK expansion
- unrelated schema churn
- speculative standards work without operational payoff
- large architectural rewrites disconnected from operator adoption
