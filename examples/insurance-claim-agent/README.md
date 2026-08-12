# Insurance Claim Agent

This example governs an AI assistant across a stateful claims workflow. It may assemble and submit a flight-cancellation claim when minimum evidence is present, while accepting a settlement is governed by a separate consequence-sensitive authority policy.

```bash
python examples/insurance-claim-agent/run.py all
```

The scenarios cover successful claim submission, missing-evidence deferral, out-of-scope claim denial, autonomous acceptance of a small settlement, human approval for a larger full-and-final settlement, and mandate revocation.

The important distinction is **prepare/submit ≠ settle**: two actions in the same workflow can have materially different authority because their consequences differ.
