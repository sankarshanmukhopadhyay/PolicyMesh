# Drift alerting and operator automation

PolicyMesh v0.17.0 upgrades the cron-friendly drift checker so that drift state changes can trigger operator automation.

## What changed

`scripts/policy_drift_check.py` now supports:

- `--state-file` to persist the previous drift status
- `--on-change-cmd` to execute an operator command only when the status changes
- `--webhook-url` to POST the drift payload to an external webhook

This keeps recurring checks cheap while making **classification changes** actionable.

## Example: local shell hook

```bash
python scripts/policy_drift_check.py https://peer.example.org ops \
  --state-file artifacts/drift/ops/state.json \
  --on-change-cmd 'printf "%s\n" "$POLICYMESH_DRIFT_PAYLOAD" >> artifacts/drift/ops/alerts.log'
```

Environment variables exported to the hook:

- `POLICYMESH_DRIFT_STATUS`
- `POLICYMESH_DRIFT_PREVIOUS_STATUS`
- `POLICYMESH_DRIFT_CHANGED`
- `POLICYMESH_DRIFT_PAYLOAD`

## Example: webhook bridge

```bash
python scripts/policy_drift_check.py https://peer.example.org ops \
  --state-file artifacts/drift/ops/state.json \
  --webhook-url https://ops.example.org/hooks/policymesh-drift
```

The payload includes the local and remote policy hashes plus a `changed` flag so downstream systems can route only the events that matter.
