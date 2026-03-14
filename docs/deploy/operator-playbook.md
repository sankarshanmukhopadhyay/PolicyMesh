# Operator Playbook

This playbook turns the PolicyMesh governance surfaces into repeatable operating motions.

## 1. Drift detected

Signals:
- `links policy drift ...`
- `links drift check ...`
- scheduled drift JSON under `artifacts/drift/...`

Response:
1. compare local and remote heads
2. run `links policy reconcile <local> <remote> <village_id>`
3. inspect `forks`, `lineage_issues`, and `selection_reason`
4. apply only the selected head that preserves deterministic lineage
5. record incident notes alongside the reconciliation artifact

## 2. Reconciliation reports a fork

Signals:
- `status = fork`
- multiple child updates for the same `previous_policy_hash`

Response:
1. stop automatic apply on the affected village
2. identify the intended governance branch
3. verify signatures and signer allowlist constraints
4. publish a corrective policy update that clearly references the desired parent
5. archive the rejected branch in incident records

## 3. Reconciliation reports a lineage gap

Signals:
- `status = lineage_gap`
- `lineage_issues` includes `missing_parent`

Response:
1. do not blindly apply the remote head
2. retrieve the missing history segment or manifest chain
3. confirm whether the gap is operator error or a malformed feed
4. re-run reconciliation after history is complete

## 4. Transparency checkpoint drift

Generate a checkpoint:

```bash
links drift checkpoint ops
```

Response:
1. compare the latest checkpoint hash across nodes
2. if hashes diverge, inspect recent transparency entries
3. confirm whether the divergence is expected rollout timing or a real inconsistency
4. preserve the checkpoint artifact for audit review

## 5. Trust anchor or signer incident

Response:
1. revoke or rotate the compromised key
2. document the event in audit artifacts
3. issue a fresh policy update signed by the approved quorum
4. distribute the updated manifest and checkpoint artifacts to peer operators

## 6. Small federation posture

For a small multi-node deployment:
- keep one operator-owned source of truth per village
- schedule periodic pull and drift checks instead of continuous churn
- exchange reconciliation and checkpoint artifacts during incidents or planned policy changes
- prefer explicit rollout windows over background auto-magic
