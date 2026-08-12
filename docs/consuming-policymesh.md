# Consuming PolicyMesh

PolicyMesh can be adopted incrementally. New integrations should choose the smallest surface that solves the current problem rather than starting with federation or a long-running service by default.

## 1. CLI: best for evaluation, CI and operator workflows

Use the `links` CLI when policies and evidence are file-oriented, when building a reproducible pilot, or when decisions should be exercised in CI.

Application action example:

```bash
links action evaluate POLICY.json REQUEST.json EVIDENCE.json \
  --authority-context AUTHORITY.json \
  --out artifacts/action-decisions/decision.json
```

Policy-governance operations remain under `links policy`, norm compilation under `links norms`, and trust-anchor operations under `links anchors`.

## 2. Python API: best for embedding a decision point

Applications and agent runtimes can call the evaluator directly:

```python
from links.sdk import ActionPolicy, evaluate_action

policy = ActionPolicy.model_validate(policy_document)
receipt = evaluate_action(
    policy,
    request=action_request,
    evidence=verified_evidence,
    authority_context=validated_authority_context,
)

if receipt.decision == "permit":
    execute_business_action()
elif receipt.decision == "defer":
    obtain_additional_authority_or_evidence()
else:
    block_business_action()
```

The application remains responsible for deciding what execution operation corresponds to a permit. PolicyMesh returns the governed decision and evidence; it does not execute a hotel booking, payment, registry mutation or agent tool merely because a permit exists.

## 3. HTTP service: best for PolicyMesh federation and operational surfaces

`links serve` exposes PolicyMesh's existing policy-feed, capability, transparency and audit endpoints. Use this surface when operating a node that must exchange or publish policy state.

The initial application-action evaluator is intentionally library/CLI-first. Exposing action evaluation as a network API should be a deployment choice because authentication, request provenance, replay protection and evidence-validation responsibilities become materially different at a remote trust boundary.

## Recommended adoption sequence

| Stage | Recommended surface | Goal |
| --- | --- | --- |
| local exploration | reference example + CLI | understand decisions and receipts |
| application pilot | Python API | embed a bounded decision point |
| governed operations | lifecycle + evidence tooling | manage policy state explicitly |
| multi-node pilot | HTTP/federation surfaces | reconcile signed policy state |
| hardened deployment | deployment profiles + assurance controls | operate with explicit security assumptions |

## Integration rule

Do not send raw assertions to PolicyMesh and assume they became trustworthy. Validate identity, registry, credential, mandate or other upstream evidence according to the system that owns those semantics, then pass the verified result into the PolicyMesh decision boundary.
