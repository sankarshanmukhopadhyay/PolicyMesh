# Risks & Mitigations

## R1 Defamation / reputational harm
Mitigation: avoid scores; publish only scoped link predicates; village policies + documentation.

## R2 Privacy violations / doxxing
Mitigation: public data only; bounded windows; retention; avoid cross-platform correlation by default.

## R3 Bias amplification
Mitigation: multi-issuer perspective; no global rank; governance and review.

## R4 Harassment / targeting
Mitigation: village-scoped visibility; token-gated endpoints; consider aggregation thresholds for public export.

## R5 Poisoning / false claims
Mitigation: signatures + bundle_id hashing; policy checks; quarantine workflows; issuer allowlists (future).

## R6 Token compromise
Mitigation: store token hashes only; rotate and revoke; prefer TLS in deployments.

## R7 Mission creep
Mitigation: explicit policy and “inference budget”; retention/minimization defaults; governance before expansion.


## Governance hardening additions

- Issuer allow/block lists per village
- Token revocation and rotation
- Quarantine + approval/rejection workflow
- Append-only audit log for decisions

## Crosswalk note

For a capability-to-risk-to-control mapping against selected external standards families, see [`docs/risk-crosswalk.md`](./risk-crosswalk.md).
