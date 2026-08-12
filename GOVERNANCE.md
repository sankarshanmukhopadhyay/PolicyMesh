# PolicyMesh Governance

## Repository authority

PolicyMesh owns the implementation semantics, schemas, command-line interfaces, evidence formats, conformance tests, and documentation published in this repository. Maintainers may approve changes to those artifacts and to repository-owned maturity declarations.

PolicyMesh does **not** create the external authority that makes a domain policy legitimate. A policy may be supplied by a trust framework, institution, community, registry, agent mandate, or other governance source. PolicyMesh can validate configured authorization conditions, execute policy transitions, federate governed state, and retain evidence of the authority context presented to it; it does not independently determine whether that external authority is substantively legitimate.

## Normative and informative artifacts

Repository schemas, lifecycle transition rules, validation behavior, and tests that assert required behavior are normative for PolicyMesh implementations. Architecture explanations, examples, crosswalks, and deployment guidance are informative unless explicitly identified otherwise.

## Change authority

Maintainers approve repository changes. Changes to lifecycle semantics, externally visible schemas, cryptographic policy, federation behavior, or evidence formats require tests and documentation in the same change. Maturity or lifecycle promotion requires evidence from the validation contract in `PROJECT-STATUS.yaml`.

## Delegation and revocation

Operational authority can be delegated through local configuration, quorum rules, signer allowlists, trust anchors, and presented authority context. Delegation remains scoped to the configured village/domain. Revocation is explicit: signer/member tokens, trust anchors, policies, and releases are revoked or superseded without erasing historical evidence.

## Conflict handling

Peer disagreement is classified as alignment, publication lag, lineage gap, fork, trust failure, incompatibility, or reconciliation failure. Local authoritative state is not silently overwritten by imported registry or peer state. Operators must explicitly apply, defer, or reject state changes.

## Release governance

A release is warranted for a new normative capability, machine-verifiable artifact, material interoperability change, completed assurance capability, adoption-ready workflow, or security/correctness fix. Formatting-only, metadata-only, and link-only changes remain commit-level changes.
