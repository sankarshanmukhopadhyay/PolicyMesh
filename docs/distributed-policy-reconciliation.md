
# Distributed Policy Reconciliation Walkthrough (Extended with Sequence + Failure Modes)

## Purpose
This document explains how PolicyMesh distributes, reconciles, and validates governance state across independent operators.

---

## System Overview

PolicyMesh is a distributed control plane where:
- policy is published as verifiable state
- nodes ingest multiple policy feeds
- reconciliation determines acceptable state
- decisions produce evidence

---

## Sequence Flow (End-to-End)

### Scenario: Normal Reconciliation

```
Node B        Node C        Node D        Node A
  |             |             |             |
  | publish h1  |             |             |
  |------------>|             |             |
  |             | publish h1  |             |
  |             |------------>|             |
  |             |             | publish h2  |
  |             |             |------------>|
  |             |             |             |
  |             |             |             | pull feeds
  |             |             |             |<-----------
  |             |             |             |
  |             |             |             | verify feeds
  |             |             |             |
  |             |             |             | compute quorum
  |             |             |             |
  |             |             |             | select h1 (2/3 support)
  |             |             |             |
  |             |             |             | emit receipt
```

### Key Observations
- No central coordinator
- Multiple competing heads
- Deterministic reconciliation outcome

---

## Reconciliation Logic

Inputs:
- candidate heads
- peer support
- trust weighting

Processing:
1. discard invalid feeds
2. group by head
3. compute support
4. apply quorum threshold

Output:
- selected head
- outcome: apply / defer / reject

---

## Malicious Peer Scenario

### Scenario

Node D attempts to inject invalid policy:

```
Node B: h1 (valid)
Node C: h1 (valid)
Node D: hX (malicious fork)
```

### Behavior

Node A performs:

1. signature verification → fails OR
2. chain continuity check → fails OR
3. insufficient quorum support → fails

### Result

```
Accepted: h1 (B, C)
Rejected: hX (D)
```

### Receipt Evidence

```json
{
  "evaluated_peers": ["B", "C", "D"],
  "accepted_head": "h1",
  "rejected_heads": ["hX"],
  "reason": "invalid_signature_or_insufficient_quorum"
}
```

---

## Drift Scenario

```
Initial:
B → h1
C → h1

Later:
C → h2
```

Node A detects:

- divergence between h1 and h2
- quorum instability

Outcome:
- defer OR switch when quorum shifts

---

## Evidence Model

Each reconciliation produces:

- selected head
- evaluated peers
- quorum details
- outcome
- signature

Properties:
- verifiable
- replayable
- portable

---

## Guarantees

### Ensured
- integrity of policy chain
- explicit reconciliation
- auditable outcomes

### Not Ensured
- global instant consistency
- unanimous agreement

---

## Commands

Pull policy:
```
links policy pull
```

Verify receipt:
```
links policy verify-receipt <path>
```

Detect drift:
```
scripts/policy_drift_check.py
```

---

## Conclusion

PolicyMesh computes governance state under distributed conditions.

It ensures:
- policy is verifiable
- reconciliation is explicit
- outcomes are provable

Governance is not declared.
It is computed and evidenced.
