# External registry interoperability

The `links.external_registry.v2` format carries registry identity, authority label, generated time, policy, members, revocations, anchors and provenance.

```bash
links registry validate registry.json
links registry diff registry.json
links registry import registry.json --decision defer
links registry import registry.json --decision apply
```

Import is never a blind overwrite. `validate` proves structural acceptability, `diff` exposes divergence, and `import` requires an explicit `apply`, `defer` or `reject` decision with a durable receipt.

## DTG/VTI registries

The PolicyMesh registry exchange schema is not a VTI Trust Registry protocol. An adapter must preserve the authoritative source, exact proposition, scope, currency and response disposition. Recognition, membership, credential provenance and authority to act are different propositions. Do not translate an unresolved or stale result into permission. See [DTG/VTI alignment](dtg.md).
