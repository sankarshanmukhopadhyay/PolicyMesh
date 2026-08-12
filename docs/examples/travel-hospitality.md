# Travel & Hospitality: governed autonomous hotel booking

The repository includes a fully runnable reference example at [`examples/travel-hospitality/`](../../examples/travel-hospitality/README.md).

## Scenario

Priya is travelling to Singapore for work. Her employer authorises `travel-agent-01` to search, reserve, modify and cancel accommodation within a defined mandate. The employer separately defines approved hotels, an autonomous nightly-rate limit and a refundable-rate requirement.

The agent proposes a specific reservation. PolicyMesh evaluates the action against:

- the traveller/agent mandate;
- employer travel policy;
- approved supplier evidence;
- hotel offer terms;
- transaction value and currency;
- the requested stay window.

The result is `permit`, `deny` or `defer` and an Action Decision Receipt.

## Why this is a useful PolicyMesh example

Travel is a multi-authority domain. The employer controls reimbursement policy, the traveller controls delegated authority, the hotel controls contractual terms, a loyalty programme may control entitlements and a payment provider controls payment authorisation. No single actor owns all of those policies.

PolicyMesh therefore operates at their decision intersection without claiming to become any of those upstream systems.

## Try it

```bash
python examples/travel-hospitality/run.py all
```

Start with `permitted-booking`, then compare `supplier-repriced`, `revoked-mandate` and `paid-upgrade-out-of-scope`. Those scenarios demonstrate respectively normal authority, changing transaction conditions, revoked authority and the separation between agent capability and delegated permission.

## Integration progression

The fixtures are intentionally synthetic. An implementation can progressively replace them with real services while preserving the same decision contract:

```text
synthetic fixture → verified external evidence → PolicyMesh decision → business API
```

Examples include a hotel sandbox API, verifiable employment evidence, a mandate service, a trust registry, loyalty entitlement credentials or an MCP/A2A agent tool surface.
