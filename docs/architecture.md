# Architecture

PolicyMesh separates **external governance authority** from **policy execution**. It receives policy and configured authority constraints, validates state transitions and approvals, distributes or reconciles state, makes bounded enforcement decisions, and produces evidence.

For adoption, it is useful to distinguish two decision layers: **policy admission** decides whether candidate policy state should be applied, deferred or rejected; **action evaluation** decides whether a specific application or agent action should be permitted, denied or deferred under the applicable policy and evidence.

```mermaid
flowchart LR
  G[External governance authority] -->|policy / mandate context| L[Lifecycle]
  L --> Q[Quorum]
  Q --> E[Enforcement]
  E --> F[Federation]
  F --> T[Transparency]
  E --> R[Decision receipts]
  L --> R
  T --> B[Evidence bundles]
  R --> B
  B --> A[Assurance consumer]
```

A peer, registry or imported artifact never gains authority merely because it is reachable. Local configured governance rules determine whether incoming state can be applied.

## Business-action decision boundary

```mermaid
flowchart LR
  I[Identity / registry / mandate / business evidence] --> D[PolicyMesh action decision]
  R[Requested application or agent action] --> D
  P[Locally applicable action policy] --> D
  D -->|PERMIT| X[Execute action]
  D -->|DENY| N[Block action]
  D -->|DEFER| H[Obtain more authority or evidence]
  D --> A[Action Decision Receipt]
```

The Travel & Hospitality reference example uses this boundary for an autonomous hotel-booking agent. The same contract can be reused by procurement, registry, agent-tool or other bounded decision domains.


## DTG interoperability boundary

PolicyMesh can sit adjacent to Decentralized Trust Graph (DTG) specifications and implementations as an executable-policy and assurance laboratory. DTG artifacts can supply evidence, governed-action semantics, ceremony outcomes, or authority constraints; PolicyMesh evaluates **locally authoritative policy** and produces decision evidence. This is an interoperability relationship, not a normative dependency.

```mermaid
flowchart LR
  D["DTG evidence / governed-action semantics"] -.->|"inputs and constraints"| P["PolicyMesh"]
  P -->|"allow / deny / defer"| I["Implementation"]
  P -->|"decision receipts + evidence"| A["Assurance"]
  A -.->|"findings / pressure-test feedback"| D
```

See [PolicyMesh and DTG](interoperability/dtg.md) for the detailed cross-workstream model and explicit non-authority boundaries.
