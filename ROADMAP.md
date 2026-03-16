## Current release focus

- [x] NormSet authoring model and compiled policy artifact lineage
- [x] Deterministic norm compiler with contradiction detection
- [x] CLI workflow for init, validate, compile, diff, and apply-compiled
- [x] Docs and examples connecting village governance to policy transport

# PolicyMesh Roadmap

This document captures the intended direction of the PolicyMesh project.
It is intentionally schedule-free. Items move forward based on architectural readiness, contributor bandwidth, and operational priority.

## Status legend
- ✅ Shipped
- 🟡 Partial
- 🔜 Planned

_Last updated: 2026-03-16_

---

## 1. Governance & Policy Evolution

### 1.1 Quorum Governance Enhancements
**Status:** 🟡 Partial
- Weighted quorum support beyond simple M-of-N acceptance
- Role-based quorum sets (for example, at least one “core” plus one “external” signer)
- Explicit quorum metadata in policy update artifacts for audit clarity

### 1.2 Policy Diff & Review
**Status:** 🟡 Partial
- Structured policy diff tooling
- Machine-readable policy change summaries
- Lifecycle semantics across proposal, approval, and activation

### 1.3 Policy Rollback & Versioning
**Status:** 🟡 Partial
- First-class policy version identifiers
- Deterministic rollback to prior policy hash
- Explicit activation time or activation height semantics across operator workflows

---

## 2. Distributed Policy Substrate

### 2.1 Pull Model Hardening
**Status:** 🟡 Partial
- Signed policy feed manifests
- Feed integrity metadata (Merkle root or hash chain)
- Pagination and large-history optimization
- Stronger end-to-end pull reconciliation rules

### 2.2 Federation & Multi-Node Reconciliation
**Status:** 🟡 Partial
- Cross-node reconciliation conflict detection
- Explicit fork detection reporting
- Durable reconciliation artifacts suitable for audit ✅
- Deterministic pull selection with lineage-gap handling ✅
- Optional gossip-style propagation

### 2.3 Trust Anchors
**Status:** 🟡 Partial
- Village-level trust anchor registry
- Anchor rotation procedures
- Explicit anchor revocation workflow
- Operator playbooks for rotation, rollover, and incident handling

---

## 3. Assurance & Observability

### 3.1 Policy Audit Trails
**Status:** 🟡 Partial
- Structured audit export (JSON/CSV)
- Policy change event classification
- Audit digest generation and signing hardening

### 3.2 Drift Monitoring
**Status:** 🟡 Partial
- Drift check CLI and severity classification ✅
- Alert hooks (webhook or CLI-based triggers)
- Periodic automated drift checks and cron-ready operator examples ✅

### 3.3 Governance Transparency
**Status:** 🟡 Partial
- Signed transparency log support ✅
- Reproducible policy history snapshots and checkpoints ✅
- Signed checkpoint publication and peer comparison ✅
- Drift class taxonomy (policy divergence vs. publication lag) ✅
- Read-only public policy endpoint hardening

---

## 4. Operational Hardening

### 4.1 Storage Layer Evolution
**Status:** 🟡 Partial
- Optional SQLite backend ✅
- Pluggable storage abstraction layer ✅
- Atomic policy apply transactions ✅

### 4.2 Deployment Profiles
**Status:** 🟡 Partial
- Single-node development profile
- Production-hardened profile guidance
- Container-ready configuration examples
- More explicit production templates and operator runbooks ✅

### 4.3 Performance & Limits
**Status:** 🟡 Partial
- Configurable rate-limit strategies
- Memory-safe handling patterns for larger claim sets
- Load testing harness and clearer performance baselines

---

## 5. Security & Risk Controls

### 5.1 Advanced Signature Controls
**Status:** 🔜 Planned
- Hardware-backed signing integration
- Key rotation enforcement
- Expiring policy updates

### 5.2 Abuse & Misuse Controls
**Status:** 🟡 Partial
- Village-level submission quotas
- Replay protection improvements
- Signed denial or rejection artifacts

### 5.3 Cryptographic Agility
**Status:** 🟡 Partial
- Algorithm metadata and guardrails
- Additional signature algorithm support
- Explicit deprecation lifecycle

### 5.4 Risk Crosswalk & Assurance Mapping
**Status:** 🟡 Partial
- Capability-to-risk-to-control mapping documented
- Selected standards-family references for operator legibility
- Machine-readable evidence and deeper control mapping remain future work

---

## 6. Ecosystem & Interoperability

### 6.1 External Registry Integration
**Status:** 🟡 Partial
- Import/export trust registry artifacts
- Registry-to-village bridging patterns

### 6.2 Standardization Alignment
**Status:** 🔜 Planned
- Schema refinement for policy update artifacts
- Optional JSON-LD or canonical context support
- Conformance coverage for policy governance

### 6.3 Tooling & SDK
**Status:** 🟡 Partial
- Python SDK wrapper
- Minimal HTTP client library
- Example integration materials
- Clearer separation between stable and experimental SDK surfaces ✅
- Machine-readable capability declarations with JSON Schema ✅
- Operator acceptance criteria for small-federation pilots ✅
