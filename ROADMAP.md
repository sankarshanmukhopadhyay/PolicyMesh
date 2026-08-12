# PolicyMesh Roadmap

This roadmap records capability state against executable evidence. A capability is marked shipped only when implementation, operator guidance and tests/evidence exist within the repository's declared scope.

**Current release:** v0.18.0  
**Last updated:** 2026-08-12

## Status legend
- ✅ Shipped
- 🔜 Planned

## 1. Governance & Policy Evolution

### 1.1 Quorum Governance Enhancements
**Status:** ✅ Shipped
- weighted quorum support;
- role-based quorum requirements;
- M-of-N support and signer allowlists;
- operator-facing quorum inspection artifacts;
- explicit quorum metadata in policy update artifacts.

### 1.2 Policy Diff & Review
**Status:** ✅ Shipped
- structured policy diff tooling;
- machine-readable policy change summaries;
- explicit proposal → approved → active lifecycle transitions;
- invalid transition rejection and lifecycle evidence artifacts.

### 1.3 Policy Rollback & Versioning
**Status:** ✅ Shipped
- first-class policy version identifiers;
- deterministic rollback to retained historical policy state;
- rollback recorded as a new governance event without deleting history;
- activation time and activation-height fields preserved in operator artifacts.

## 2. Distributed Policy Substrate

### 2.1 Pull Model Hardening
**Status:** ✅ Shipped
- signed policy-feed manifests;
- feed integrity metadata;
- pagination and history-gap recovery;
- manifest trust policy;
- deterministic selection and reconciliation evidence.

### 2.2 Federation & Multi-Node Reconciliation
**Status:** ✅ Shipped within declared scope
- conflict and fork detection;
- durable reconciliation artifacts;
- lineage-gap handling;
- checkpoint/manifest based peer change notification and pull reconciliation.

PolicyMesh deliberately does not implement an unconstrained epidemic gossip network. Peers may signal that newer state exists; the receiving node independently fetches, validates and decides whether to apply it.

### 2.3 Trust Anchors
**Status:** ✅ Shipped
- village-level append-only trust-anchor registry;
- register, rotate, revoke, inspect and history workflows;
- historical entries retained after revocation;
- operator guidance for rollover and incident handling.

## 3. Assurance & Observability

### 3.1 Policy Audit Trails
**Status:** ✅ Shipped
- structured JSON and CSV audit export;
- event/action classification;
- deterministic SHA-256 digests and optional signing;
- evidence-bundle packaging.

### 3.2 Drift Monitoring
**Status:** ✅ Shipped
- drift CLI and severity taxonomy;
- webhook/CLI alert hooks;
- periodic/cron-ready operator examples;
- publication-lag vs policy-divergence classification.

### 3.3 Governance Transparency
**Status:** ✅ Shipped
- signed transparency log/checkpoints;
- reproducible snapshots and peer comparison;
- live read-only checkpoint endpoint;
- explicitly opt-in read-only public policy endpoint;
- tests preventing mutation through public surfaces.

## 4. Operational Hardening

### 4.1 Storage Layer Evolution
**Status:** ✅ Shipped
- optional SQLite backend;
- pluggable storage abstraction;
- atomic policy apply transactions.

### 4.2 Deployment Profiles
**Status:** ✅ Shipped
- development profile;
- federation-pilot profile;
- production-hardened guidance profile;
- container and operator guidance.

### 4.3 Performance & Limits
**Status:** ✅ Shipped within declared scope
- fixed-window and token-bucket strategy configuration;
- bounded pagination and submission quotas;
- load-test harness;
- operational guidance for memory-safe bounded workloads.

Reference results are not production performance guarantees.

## 5. Security & Risk Controls

### 5.1 Advanced Signature Controls
**Status:** ✅ Shipped within declared scope
- explicit key and trust-anchor rotation/revocation workflows;
- expiring policy-update enforcement fields;
- environment-backed signing integration.

Hardware-backed signing remains deployment/integration specific and is not claimed as a native PolicyMesh capability.

### 5.2 Abuse & Misuse Controls
**Status:** ✅ Shipped
- village submission quotas;
- bearer/member revocation and duplicate/replay-aware bounded workflows;
- signed denial/rejection artifacts;
- deterministic decision receipts.

### 5.3 Cryptographic Agility
**Status:** ✅ Shipped
- algorithm metadata and guardrails;
- Ed25519 and ECDSA P-256 implementation support;
- supported/deprecated/prohibited lifecycle;
- unknown algorithms fail closed.

### 5.4 Risk Crosswalk & Assurance Mapping
**Status:** ✅ Shipped
- capability → risk → control → test → evidence mappings;
- selected standards-family references for operator legibility;
- machine-readable evidence maps;
- crosswalks are informative and do not assert external compliance.

## 6. Ecosystem & Interoperability

### 6.1 External Registry Integration
**Status:** ✅ Shipped
- versioned export schema;
- validate and diff workflows;
- explicit apply/defer/reject import decision;
- local authoritative state is never silently overwritten;
- trust-anchor and provenance carriage.

### 6.2 Standardization Alignment
**Status:** ✅ Shipped within declared scope
- JSON Schema contracts for externally exchanged artifacts;
- policy governance conformance tests;
- controlled evidence and authority-boundary semantics.

JSON-LD is not required for the v0.18.0 interoperability contract and remains an optional future profile rather than a completion dependency.

### 6.3 Tooling & SDK
**Status:** ✅ Shipped
- Python SDK façade;
- minimal HTTP client;
- capability/checkpoint workflows;
- machine-readable capability manifest;
- stable vs experimental surface documentation;
- small-federation pilot acceptance guidance.

## Next horizon

### 7. Authority-context interoperability — 🔜 Planned
Typed profiles for principal, actor, mandate, delegation scope, constraints and revocation references while preserving external authority boundaries.

### 8. Evidence-bundle exchange profiles — 🔜 Planned
Cross-implementation evidence bundle transport, detached signatures and verifier profiles.

### 9. Independent conformance levels — 🔜 Planned
Named conformance levels with requirement IDs, test vectors and retained execution provenance.

### 10. Policy simulation and impact analysis — 🔜 Planned
Evaluate prospective policy changes against recorded scenarios before activation.

### 11. Multi-domain policy composition — 🔜 Planned
Explicit conflict semantics when independently authoritative domains contribute constraints.

### 12. Privacy-preserving evidence — 🔜 Planned
Selective/minimized assurance evidence that proves decision properties without unnecessary disclosure.
