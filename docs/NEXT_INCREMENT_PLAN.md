# Next Increment Plan — Feed Integrity Hardening and Operator Automation

The v0.16.0 release closes the largest operational gap from the prior roadmap by exposing live checkpoint and capability endpoints, adding quorum inspection, and stabilizing the public SDK surface.

## Objective

Advance from discoverable operator surfaces to stronger federation trust guarantees and more automation-ready operational workflows.

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
