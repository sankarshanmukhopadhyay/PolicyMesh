# Evidence bundles

`policymesh.evidence.v1` packages existing decision and operational artifacts into a portable directory with a manifest and SHA-256 digests.

```bash
links evidence build --village-id example --event-id evt-001 --source receipt.json --source reconciliation.json
links evidence verify artifacts/evidence/example/evt-001
```

Verification detects missing or modified artifacts. A valid bundle proves artifact integrity relative to its manifest; it does not by itself prove the legitimacy of an external governance authority.
