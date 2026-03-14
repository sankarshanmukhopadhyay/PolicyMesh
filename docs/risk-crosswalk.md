# Governance Risk Crosswalk

This document maps PolicyMesh system capabilities to operational risks, control objectives, and selected external standards families.

The goal is not to claim certification or comprehensive control coverage. The goal is to make the architecture legible to operators, reviewers, and institutions that need a clearer account of what the system is trying to protect against.

## Scope and intent

PolicyMesh is not a generic compliance platform. It is a small-footprint governance substrate for verifiable claim bundles, village-scoped policy control, quarantine review, audit traces, and policy synchronization.

This crosswalk therefore focuses on:

- system capabilities already present in the repository or clearly documented as partial
- the main risks those capabilities are intended to reduce
- control objectives that can be understood operationally
- selected reference points from widely used frameworks

This document is a thin mapping layer. It is not a substitute for a full risk assessment, threat model, or formal conformance program.

## Method

The mapping uses the following pattern:

1. **Capability**: what the system does
2. **Risk addressed**: the problem or failure mode the capability helps reduce
3. **Control objective**: the assurance goal the operator should be able to articulate
4. **Reference families**: external standards or governance frameworks with related control intent

## Control-family references used here

The mappings below use selected references from:

- **NIST AI RMF 1.0** for governance, mapping, and monitoring intent
- **NIST SP 800-53 Rev. 5** for security and assurance control families
- **ISO/IEC 27001:2022 Annex A** for organizational and technical security controls
- **Trust over IP** governance and trust-registry-aligned concepts for policy provenance and authority handling

These are directional alignments, not claims of full coverage.

## Master crosswalk

| Capability | Risk addressed | Control objective | NIST AI RMF | NIST SP 800-53 | ISO/IEC 27001 | ToIP-aligned concept |
|---|---|---|---|---|---|---|
| Signed claim bundles | forged or altered claim artifacts | preserve claim integrity and issuer-bound provenance | Govern, Measure | SI-7, SC-12, SC-13 | A.8.24, A.8.25 | Verifiable artifact integrity |
| Village-scoped policy controls | uncontrolled claim acceptance across contexts | ensure acceptance rules are explicit, bounded, and locally governed | Govern | AC-3, AC-6, CM-3 | A.5.1, A.5.15 | Governance-defined trust perimeter |
| Quarantine workflow | unsafe or non-conforming bundles entering the main store | prevent automatic acceptance of policy-failing artifacts | Govern, Manage | SI-3, SI-4, CA-7 | A.5.24, A.8.16 | Human review safety valve |
| Append-only audit log | inability to reconstruct decisions or investigate incidents | maintain inspectable records of governance and ingestion actions | Govern, Measure | AU-2, AU-3, AU-6, AU-12 | A.8.15, A.8.16 | Accountability and decision trace |
| Policy update signing | unauthorized policy changes or forged governance artifacts | authenticate governance changes and preserve provenance | Govern | IA-3, IA-5, CM-5, SC-12 | A.5.16, A.8.24 | Signed governance artifacts |
| Quorum-based policy approval | unilateral or weakly reviewed policy mutation | require multi-party authorization for sensitive policy changes | Govern | CM-3, CM-5, AC-3 | A.5.2, A.5.3, A.5.15 | Multi-party governance approval |
| Policy diff and change summaries | opaque policy change impact | make governance deltas inspectable before or after activation | Govern, Map | CM-3, CM-9, AU-6 | A.5.8, A.8.32 | Reviewable policy lifecycle |
| Pull reconciliation and drift detection | silent divergence between local and remote policy state | detect unauthorized or unplanned policy drift | Govern, Measure | SI-4, CA-7, CM-6 | A.8.16, A.8.9 | Policy state convergence monitoring |
| Trust anchor registry and rotation | authority confusion or stale signing trust roots | manage which authorities are trusted and when that trust changes | Govern | IA-5, SC-12, SC-17 | A.5.17, A.8.24 | Trust anchor management |
| Token-gated management endpoints | unauthorized operational access | ensure management actions require explicit authentication | Govern | AC-2, AC-3, IA-2 | A.5.15, A.5.16 | Controlled operator access |
| Exportable audit artifacts | weak external review and poor evidence portability | support inspection, reporting, and downstream assurance workflows | Measure | AU-6, CA-7 | A.5.35, A.8.16 | Portable governance evidence |

## Capability notes

### Signed claim bundles

**What it covers**
- claim artifact signing and integrity checks
- issuer-bound provenance for submitted material

**Primary risks reduced**
- artifact tampering
- casual forgery
- loss of provenance during exchange

**Residual gaps**
- stronger algorithm agility and lifecycle policy remain partial
- hardware-backed signing is not yet part of the default posture

### Village policy controls

**What it covers**
- policy-bounded claim acceptance
- local norms on predicates, windows, and acceptance behavior

**Primary risks reduced**
- uncontrolled aggregation
- mission creep through silent scope expansion
- one-size-fits-all acceptance logic across different communities

**Residual gaps**
- richer lifecycle semantics are still hardening
- policy federation across nodes remains partial rather than fully mature

### Quarantine and review

**What it covers**
- holding area for policy-failing or context-mismatched bundles
- explicit approve or reject path before ingestion

**Primary risks reduced**
- unsafe automatic ingestion
- irrecoverable acceptance errors
- weak operator response to suspicious inputs

**Residual gaps**
- richer denial artifacts and broader incident-response playbooks remain future work

### Audit and export

**What it covers**
- append-only decision traces
- exportable audit material for downstream analysis

**Primary risks reduced**
- poor post-incident reconstruction
- weak governance accountability
- limited evidence portability

**Residual gaps**
- stronger audit digest signing and production evidence packaging remain partial

### Policy signing and quorum approval

**What it covers**
- signed policy updates
- M-of-N quorum today, with weighted and role-based models in partial state

**Primary risks reduced**
- unilateral policy mutation
- weak governance provenance
- poor reviewability of sensitive changes

**Residual gaps**
- richer lifecycle handling across proposal, approval, and activation is still being hardened
- operational playbooks for quorum failure and emergency rollback should be expanded

### Drift detection and reconciliation

**What it covers**
- pull-and-apply model
- drift check CLI
- deterministic reconciliation rule based on update metadata

**Primary risks reduced**
- unnoticed policy divergence
- local state drifting away from expected remote state
- operator confusion about current policy version

**Residual gaps**
- signed feed manifests and large-history handling are partial
- durable conflict and fork artifacts remain a next priority

### Trust anchors

**What it covers**
- anchor registration
- rotation and revocation primitives

**Primary risks reduced**
- stale authority assumptions
- continuing trust in compromised or retired signers
- unclear boundary between recognized and unrecognized governance authorities

**Residual gaps**
- operator playbooks for rollover and incident handling should be expanded

## Risk themes and architecture implications

A few themes matter more than the rest.

### 1. Governance integrity

PolicyMesh is unusual because policy is not merely configuration. Policy is part of the system's governance substrate. That means policy authenticity, reviewability, rollback, and drift monitoring are not nice extras. They are first-order controls.

### 2. Evidence portability

The system becomes more institutionally useful when it can produce portable evidence of what happened, why it happened, and under which policy state it happened. Audit export, signed governance artifacts, and clear policy history are all steps in that direction.

### 3. Bounded trust, not universal trust

Village-level controls, signer allowlists, and trust anchors show that PolicyMesh is operating with bounded and contextual trust. That is the right posture for a system dealing with reputation-adjacent or governance-sensitive artifacts.

## What this crosswalk does not claim

This document does not claim:

- full NIST SP 800-53 control coverage
- ISO/IEC 27001 conformity
- AI system safety certification
- legal or sector-specific compliance readiness by default

Any such claim would require a fuller control set, implementation evidence, operating procedures, and environment-specific review.

## Practical next steps

The highest-value follow-on work would be:

1. add a machine-readable control mapping artifact for major governance events
2. package audit exports and policy state snapshots into portable evidence bundles
3. add durable conflict and fork report artifacts for reconciliation events
4. document operator response playbooks for drift, anchor rotation, and quarantine escalation

That is the path from descriptive governance to operational assurance.
