# Personal Shopping Agent

This example asks: **may my AI shopping agent create this exact financial commitment on my behalf?**

The agent may discover and recommend products broadly, but `purchase_item` is gated by an active mandate, allowed category, trusted merchant, commitment type, currency and autonomous spending threshold. A purchase within ₹5,000 can be permitted; a larger purchase is deferred for fresh user approval; prohibited categories, recurring commitments, untrusted merchants or revoked authority are denied.

```bash
python examples/personal-shopping/run.py all
```

The example demonstrates the personal-agent authority ladder: **observe → recommend → prepare → commit**. PolicyMesh is applied at the consequential `commit` boundary rather than treated as a search/recommendation engine.

Every run writes an Action Decision Receipt under `examples/personal-shopping/artifacts/`.
