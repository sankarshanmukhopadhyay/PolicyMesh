# Next Increment Plan — Policy Convergence and Operational Durability

This document describes the next coherent increment for Links.
It is forward-looking only and avoids duplicating already-shipped work.

## Objective

Close the gap between a working local governance substrate and a more durable multi-node operating model.

---

## Priority 1: Reconciliation hardening

Strengthen the pull-based policy path so that nodes can converge more safely and operators can understand disagreements.

### Target outcomes
- Harden `links policy pull --apply` behavior for repeatable convergence.
- Produce explicit conflict and fork report artifacts suitable for audit and debugging.
- Make feed pagination and history traversal easier to operate at larger history depths.
- Clarify deterministic tie-break and replay behavior in docs and examples.

---

## Priority 2: Storage abstraction

Reduce the operational fragility of a filesystem-only posture without breaking the small-footprint default.

### Target outcomes
- Introduce a storage abstraction boundary that preserves the current default backend.
- Add an optional SQLite backend.
- Define atomic apply semantics across policy state, audit records, and derived indexes.
- Keep migration and rollback simple for operators.

---

## Priority 3: Drift and transparency automation

Move from manual inspection toward routine operational checks.

### Target outcomes
- Add cron-friendly drift automation examples.
- Improve webhook and alerting guidance.
- Strengthen transparency snapshot and checkpoint handling.
- Document expected operator responses for drift, mismatch, and anchor events.

---

## Priority 4: Production deployment guidance

Push deployment docs from “good guidance” toward “repeatable operator playbook.”

### Target outcomes
- Expand production examples for reverse proxy, tokens, and logging.
- Clarify scale limits of the in-memory safety mechanisms.
- Add concrete deployment patterns for single-node and small federated environments.
- Align operational docs with shipped versus planned capabilities.

---

## Explicit non-goals for this increment

These items are valuable, but they should not be mixed into the same commit train unless needed for implementation:

- broad repository layout refactors
- wholesale vendoring from upstream
- speculative standards alignment work that does not improve current operation
- large SDK surface expansion unrelated to reconciliation or storage
