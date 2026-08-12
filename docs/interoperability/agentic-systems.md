# Agentic-system interoperability

PolicyMesh is not an agent identity, registry or delegation protocol. Its useful boundary is narrower: a policy update may carry an optional `authority_context` recording the principal, actor, mandate, delegation, scope, constraints, validity or revocation references presented when a policy decision was made.

This preserves the architectural distinction:

**Identity ≠ authority ≠ delegation ≠ permission ≠ policy decision.**

An external agent registry, mandate system, governance model or trust framework remains responsible for validating its own authority semantics. PolicyMesh can consume the resulting constraints and retain decision evidence without silently acquiring that authority.


For the broader relationship to DTG Trust Tasks, ceremonies, credentials, proofs and assurance work, see [PolicyMesh and DTG](dtg.md).

## Personal-agent profile

For personal AI agents, a useful enforcement position is immediately before an MCP/API/tool invocation that creates consequential external state. The agent proposes an action; PolicyMesh evaluates the action policy, authority context and evidence; only `PERMIT` proceeds to execution. `DEFER` causes the agent to obtain approval or missing evidence and re-evaluate; `DENY` blocks the candidate.

See [PolicyMesh for personal-agent governance](../concepts/personal-agent-governance.md) and the runnable Shopping, Healthcare and Insurance examples.
