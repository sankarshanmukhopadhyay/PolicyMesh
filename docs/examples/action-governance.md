---
title: Minimal execution walkthrough
parent: Governance case studies
nav_order: 6
---

# Run a governed action from decision to evidence

From the repository root, use Python 3.12 and install the project:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python examples/action_governance.py
```

Expected output:

```text
allowed permit
deferred defer
revoked deny
missing deny
executed: ['allowed']
```

The example uses simulated authority and an in-memory side effect, not a real purchase. It blocks invalid input, denial and deferral. Verification is local reproduction, not an authorization source. Real consumers must authenticate the principal and mandate, establish freshness and bind the exact operation at execution time. Re-evaluate if material facts change.

For a file-oriented workflow use the existing travel or personal-shopping fixtures with `links action evaluate`, then `links action verify-decision RECEIPT.json POLICY.json REQUEST.json EVIDENCE.json AUTHORITY.json`. Retain the exact inputs securely; use explicit empty JSON objects where appropriate. A successful evaluate command does not imply permit. A successful verification command does not imply fresh permission.

Run `python scripts/action_conformance.py` to reproduce the implementation evidence. See [action semantics](../concepts/action-evaluation.md) and [receipt verification](../decision-receipts.md).
