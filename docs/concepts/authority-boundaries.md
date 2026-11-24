# Authority boundaries

PolicyMesh can answer whether a configured signer, quorum, anchor, policy state or peer artifact satisfies PolicyMesh rules. It cannot by itself answer whether the external institution, trust framework, human principal or agent mandate that supplied those rules is legitimate.

`authority_context` therefore records presented context as evidence. It may contain principal, actor, mandate, delegation scope, constraints, validity and revocation references, but consumers must validate those semantics with the authoritative external system or profile.

For application-action evaluation, this means PolicyMesh may enforce that an action is within a presented mandate and may record the mandate digest in its receipt. That does **not** mean PolicyMesh issued the mandate or independently established the legitimacy of the principal, employer, registry or agent relationship.


## DTG boundary

The same rule applies when PolicyMesh is integrated with Decentralized Trust Graph work. A Trust Task, ceremony receipt, credential, proof, registry record, or other DTG artifact does not acquire new authority merely because PolicyMesh can consume it. The originating specification or governance system retains authority over its own semantics; PolicyMesh is authoritative only for the policy decision made under its configured local rules.

See [PolicyMesh and DTG](../interoperability/dtg.md).

VTI explicitly separates native access-control grants, approval authority and acting delegation. A DTG VAC grants scoped authority in its subject's own name; it is not itself delegation on behalf of an issuer. PolicyMesh consumes normalized facts without verifying those propositions. Local permission cannot override native refusal, and reproduced decisions cannot establish semantic completion or fresh authority.
