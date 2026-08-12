# Worked examples

PolicyMesh examples are executable governance cases, not screenshots or pseudo-code. Each vertical supplies requests, evidence, authority context, action policy, expected outcomes and receipt-producing runners.

| Example | Governance problem | Personal-agent role |
| --- | --- | --- |
| [Travel & Hospitality](travel-hospitality/README.md) | multi-party policy intersection and changing contractual state | search, book, modify and cancel travel within mandate |
| [Personal Shopping](personal-shopping/README.md) | bounded purchasing authority and escalation | discover freely, commit only inside budget/category/supplier constraints |
| [Healthcare Appointment & Consent](healthcare-agent/README.md) | purpose limitation, provider trust and sensitive disclosure | schedule care and release only policy-permitted data |
| [Insurance Claim](insurance-claim-agent/README.md) | evidence-gated workflow and settlement authority | assemble/submit claims and accept only bounded settlements |

Run any example with `python examples/<example>/run.py all`.

These verticals deliberately reuse the same `ActionPolicy → evaluate_action → ActionDecisionReceipt` contract. Industry-specific identity, registries, mandates and execution APIs remain outside PolicyMesh and are represented by deterministic fixtures so the governance boundary is inspectable.
