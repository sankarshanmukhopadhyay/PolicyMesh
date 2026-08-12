# Security Policy

## Scope

PolicyMesh handles signed governance artifacts, trust anchors, policy updates, claim bundles, public read surfaces, reconciliation data, and evidence outputs. Security reports should identify the affected component, version/commit, reproduction steps, expected impact, and any evidence demonstrating exploitability.

## Security boundaries

PolicyMesh does not treat network transport, external governance legitimacy, operator identity proofing, HSM custody, or third-party registry correctness as automatically trusted. Production deployments should use TLS termination, least-privilege credentials, protected signing keys, explicit signer/anchor policies, bounded public surfaces, rate limits, replay controls, retained audit evidence, and monitored reconciliation.

## Cryptographic policy

Algorithm acceptance is governed rather than inferred. `ed25519` and `ecdsa_p256` are currently supported by the cryptographic policy layer. Unknown or prohibited algorithms fail closed. Deprecation is an explicit lifecycle state and must not silently widen acceptance.

## Disclosure

Do not open a public issue containing active secrets, private keys, tokens, or exploit material that would materially increase risk before remediation. Use the repository owner's private security-reporting channel when available.
