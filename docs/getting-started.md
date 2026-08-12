# Getting started: from governance intent to a decision

PolicyMesh is easiest to understand as a **governed decision substrate**. A useful first mental model is not “a federation toolkit”; it is a sequence:

```text
governance intent → executable policy → action or policy candidate → decision → durable evidence
```

## Choose your entry point

### I want to understand the project

Read, in order:

1. this page;
2. [Architecture](architecture.md);
3. [Authority boundaries](concepts/authority-boundaries.md);
4. the [Travel & Hospitality example](examples/travel-hospitality.md).

### I want to run something meaningful

Install PolicyMesh, then run the travel example:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e . pytest
python examples/travel-hospitality/run.py all
```

This produces real `permit`, `deny` and `defer` decisions and integrity-verifiable receipts without requiring any external service.

### I am integrating an existing trust or business system

Treat PolicyMesh as a boundary component. Keep identity, legitimacy, mandates, registries and business APIs authoritative in their own systems. Supply their verified outputs as policy inputs/evidence, let PolicyMesh make a locally authoritative decision, and retain the resulting receipt.

A practical decomposition is:

| Existing system owns | PolicyMesh consumes |
| --- | --- |
| identity provider | verified subject/actor facts |
| delegation or mandate service | authority scope and status |
| registry | supplier/member/status evidence |
| governance body | locally applicable policy |
| application / agent | requested action |
| PolicyMesh | decision and evidence |

## Two decision layers

New readers should distinguish two different things PolicyMesh can decide.

**Policy admission** asks whether a policy update from a peer should be applied, deferred or rejected. This is the existing federation/policy-lifecycle decision flow and produces a Policy Decision Receipt.

**Action evaluation** asks whether a specific application action should be permitted, denied or deferred under a declared action policy and evidence set. It produces an Action Decision Receipt.

These layers complement each other. A node may first establish which policy is active, then use that active policy to govern business or agent actions.

## Minimal action decision

```bash
links action evaluate POLICY.json REQUEST.json EVIDENCE.json \
  --authority-context AUTHORITY.json \
  --out artifacts/action-decisions/decision.json
```

Verify the receipt:

```bash
links action verify-receipt artifacts/action-decisions/decision.json
```

## What to adopt first

For a first pilot, avoid deploying every PolicyMesh feature. Start with:

1. one bounded decision domain;
2. one explicit authority source;
3. a small versioned policy;
4. deterministic fixtures for requests and evidence;
5. permit/deny/defer tests;
6. retained decision receipts;
7. only then add federation, signed feeds, trust anchors and external evidence exchange.

That sequence keeps the governance boundary observable while avoiding premature distributed-system complexity.
