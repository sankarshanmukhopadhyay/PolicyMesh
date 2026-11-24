---
title: Cross-domain failure analysis
parent: Governance case studies
nav_order: 7
---

# Cross-domain failure analysis

The reviewed [DTFC baseline](https://github.com/qbf-consulting/digital-trust-failure-corpus/tree/1eda75842cf3b268361dc47ce8ade23b6a99c5cb) provides reusable draft failure propositions. PolicyMesh illustrates selected mechanisms; it does not assert coverage of canonical case preconditions or falsification criteria. No corpus records are imported or modified.

| Mechanism | DTFC case | Local capability and limitation |
|---|---|---|
| Stale authority | [DTF-001](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/authority/DTF-001.json), [DTF-011](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/evidence/DTF-011.json) | Supplied state can be evaluated; freshness and actual revocation propagation external |
| Scope escalation | [DTF-002](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/authority/DTF-002.json) | Action and scope predicates; authoritative delegation derivation external |
| Missing evidence | [DTF-010](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/evidence/DTF-010.json) | Required operands fail closed; source authentication external |
| Changed action or approval | [DTF-015](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/authority/DTF-015.json), [DTF-017](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/authority/DTF-017.json) | Re-evaluation and local binding possible; native approval redemption external |
| Historical basis | [DTF-019](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/authority/DTF-019.json) | Reproduce retained decision; historical authority requires independently retained evidence |
| Decision resolution | [DTF-029](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/evidence/DTF-029.json), [DTF-030](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/evidence/DTF-030.json), [DTF-031](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/lifecycle/DTF-031.json) | Re-evaluate changed inputs; distinguish evidence changes from authority changes |
| Privacy | [DTF-034](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/privacy/DTF-034.json), [DTF-037](https://github.com/qbf-consulting/digital-trust-failure-corpus/blob/1eda75842cf3b268361dc47ce8ade23b6a99c5cb/corpus/privacy/DTF-037.json) | Minimize evaluated inputs and protect receipts; onward-use enforcement external |

DTFC PASS/DENY/INDETERMINATE are propositions in a consuming context; PolicyMesh permit/deny/defer are local action decisions. They are not interchangeable. A local denial or deferral may be safe for a particular failure illustration but does not prove the whole DTFC case.

## Policy review priorities

Establish exact action and authority scope, freshness, approval binding, resolution evidence, execution idempotency and audit retention. Identify harms from both false permit and false refusal, including delay, financial loss and denial of care. Decide who owns escalation and remediation. Record external controls separately from executable rules.
