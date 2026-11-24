---
title: Synthetic VTI local policy gate
nav_order: 9
---

# Synthetic VTI-oriented local policy gate

This offline example illustrates the supplementary application decision boundary described in [PolicyMesh and DTG/VTI](dtg.md). It is not a VTI adapter, native Trust Task, credential verifier or conformance test of an upstream implementation.

From the repository root, with the project installed:

```bash
python examples/vti_local_gate.py
python -m pytest tests/test_vti_local_gate.py
```

Expected output:

```text
eligible permit verified True
native-refusal deny verified False
stale deny verified False
unresolved-approval defer verified False
local-refusal deny verified False
```

The last column denotes eligibility to proceed to the native execution boundary, not execution. The example derives a SHA-256 digest of the complete local candidate and rejects a caller-supplied binding. The digest is not a canonical VTI wire-payload digest. Freshness and authority facts are synthetic, not authenticated determinations. A real adapter must derive them from independently authenticated, current, operation-bound inputs and must preserve upstream refusal or indeterminate status. A caller-supplied boolean is not adequate evidence.

The tests additionally exercise actor substitution, changed operation or resource, caller-supplied digest, missing native authority and mismatched approval. The local receipt verifier reproduces both permit and non-permit outcomes but leaves external authority and issuer authentication unassessed. Single-use approval redemption, expiry, native audit, replay and actual task completion are external responsibilities. A real integration must enforce those requirements at the operation boundary.

The test IDs PM-VTI-001 to PM-VTI-009 identify local regression cases only. They do not represent upstream VTI requirement satisfaction. See the pinned source baseline and informative mapping in the parent guide.
