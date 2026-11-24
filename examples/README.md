# Executable governance case studies

These fictional but realistic transaction patterns support policy design, failure analysis and local implementation testing. Start with the reader-facing case studies, then run the corresponding offline fixtures.

| Domain | Reader guide | Execution |
|---|---|---|
| Travel | [Journey, policy and failures](../docs/examples/travel-hospitality.md) | [Travel runner](travel-hospitality/README.md) |
| Shopping | [Journey, policy and failures](../docs/examples/personal-shopping.md) | [Shopping runner](personal-shopping/README.md) |
| Healthcare | [Journey, policy and failures](../docs/examples/healthcare-agent.md) | [Healthcare runner](healthcare-agent/README.md) |
| Insurance | [Journey, policy and failures](../docs/examples/insurance-claim-agent.md) | [Insurance runner](insurance-claim-agent/README.md) |

Install from the repository root with `pip install -e ".[dev]"`, then run `python examples/<domain>/run.py all`. The scenario indexes link requests to expected outcomes and illustrative DTFC correlations. See the [authoring guidance](_shared/scenario-authoring.md).

Every domain uses the same ActionPolicy, evaluator and receipt contract. The runners do not perform external business transactions. Read the [minimal execution walkthrough](../docs/examples/action-governance.md) and [synthetic VTI gate](../docs/interoperability/vti-local-gate.md) for additional integration patterns.
