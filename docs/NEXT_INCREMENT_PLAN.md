# Next Increment Plan — Rollback Orchestration and Feed Trust Deepening

The v0.17.0 release closes a major evidence gap by introducing machine-verifiable policy decision receipts, lifecycle-aware admission outcomes, and alertable drift automation.

## Objective

Advance from evidence-producing operator workflows to stronger rollback orchestration, deeper feed trust guarantees, and richer promotion semantics.

---

## Priority 1: Feed integrity hardening

### Target outcomes
- Tighten signed policy feed manifest verification and trust-pinning workflows.
- Expand parent-chain recovery and unresolved-history reporting for long pull histories.
- Add more explicit operator artifacts for manifest trust failures, lineage gaps, and fork conditions.

---

## Priority 2: Alertable drift and reconciliation workflows

### Target outcomes
- Add webhook- or command-hook based alert surfaces for drift classification changes.
- Provide operator-ready scheduled examples for pull, drift, and checkpoint comparison.
- Improve durable reconciliation output so operators can distinguish publication lag, policy divergence, and trust failure faster.

---

## Priority 3: Quorum metadata and review discipline

### Target outcomes
- Tighten quorum metadata requirements for higher-assurance deployments.
- Expand worked examples for weighted and role-based quorum review procedures.
- Clarify lifecycle semantics across proposal, approval, activation, and rollback.

---

## Explicit non-goals for this increment

- New storage backends beyond filesystem and SQLite
- Broad schema redesign without an operator-facing payoff
- New standards alignment work that does not improve federation operations

## Priority 4: Rollback orchestration and promotion workflows

### Target outcomes
- Add operator-guided rollback proposals with durable receipts and explicit activation windows.
- Distinguish promotion, deferred activation, and rollback pathways in CLI workflows, not just in artifact fields.
- Expand worked examples for proposal to approval to activation transitions under higher-assurance village policies.
