# Personal Shopping Agent

A personal agent can discover freely but create purchases only inside user-defined category, merchant, commitment and spending constraints.

## Run it

```bash
python examples/personal-shopping/run.py all
```

The runner compares every result with the expected decision and writes integrity-verifiable Action Decision Receipts under the example's `artifacts/` directory.

## Inspect the implementation

See [`examples/personal-shopping/README.md`](../../examples/personal-shopping/README.md) for the scenario model, then inspect `policy/`, `authority/`, `evidence/`, `requests/` and `expected/`. The fixtures intentionally keep upstream services synthetic so the policy boundary is deterministic and offline.

Continue with [PolicyMesh for personal-agent governance](../concepts/personal-agent-governance.md) to see the shared architecture across examples.
