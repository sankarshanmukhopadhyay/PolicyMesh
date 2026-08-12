# Healthcare Appointment & Consent

Scheduling and sensitive disclosure are governed separately so appointment authority does not silently become blanket health-data authority.

## Run it

```bash
python examples/healthcare-agent/run.py all
```

The runner compares every result with the expected decision and writes integrity-verifiable Action Decision Receipts under the example's `artifacts/` directory.

## Inspect the implementation

See [`examples/healthcare-agent/README.md`](../../examples/healthcare-agent/README.md) for the scenario model, then inspect `policy/`, `authority/`, `evidence/`, `requests/` and `expected/`. The fixtures intentionally keep upstream services synthetic so the policy boundary is deterministic and offline.

Continue with [PolicyMesh for personal-agent governance](../concepts/personal-agent-governance.md) to see the shared architecture across examples.
