#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import requests

from links.policy_updates import VillagePolicyUpdate, compute_policy_hash
from links.villages import load_village


def main() -> int:
    parser = argparse.ArgumentParser(description='Cron-friendly policy drift check for PolicyMesh operators.')
    parser.add_argument('url', help='Base URL of remote PolicyMesh node')
    parser.add_argument('village_id', help='Village identifier')
    parser.add_argument('--data-root', default='data', help='Local PolicyMesh data root (default: data)')
    parser.add_argument('--token', default=None, help='Bearer token for remote access')
    parser.add_argument('--out', default=None, help='Output JSON path (default: artifacts/drift/<village_id>/drift.<timestamp>.json)')
    parser.add_argument('--state-file', default=None, help='Path to persisted prior status for change detection')
    parser.add_argument('--on-change-cmd', default=None, help='Shell command to execute when status changes')
    parser.add_argument('--webhook-url', default=None, help='Webhook URL to POST the payload to when status changes')
    args = parser.parse_args()

    base = args.url.rstrip('/')
    endpoint = f"{base}/villages/{args.village_id}/policy/latest"
    headers = {}
    if args.token:
        headers['Authorization'] = f'Bearer {args.token}'

    r = requests.get(endpoint, headers=headers, timeout=30)
    r.raise_for_status()
    remote = VillagePolicyUpdate.model_validate(r.json())

    village = load_village(Path(args.data_root), args.village_id)
    local_hash = compute_policy_hash(village.policy.model_dump())
    remote_hash = remote.policy_hash

    previous_status = None
    state_path = Path(args.state_file) if args.state_file else None
    if state_path and state_path.exists():
        try:
            previous_status = json.loads(state_path.read_text(encoding='utf-8')).get('status')
        except Exception:
            previous_status = None

    payload = {
        'village_id': args.village_id,
        'checked_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'local_policy_hash': local_hash,
        'remote_policy_hash': remote_hash,
        'drift': local_hash != remote_hash,
        'status': 'drift' if local_hash != remote_hash else 'aligned',
        'source_url': base,
        'previous_status': previous_status,
    }
    payload['changed'] = previous_status is not None and previous_status != payload['status']

    out = Path(args.out) if args.out else Path('artifacts/drift') / args.village_id / f"drift.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')

    if state_path:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({'status': payload['status'], 'checked_at': payload['checked_at']}, indent=2) + '\n', encoding='utf-8')

    if payload['changed'] and args.webhook_url:
        try:
            requests.post(args.webhook_url, json=payload, timeout=15).raise_for_status()
        except Exception as exc:
            payload['webhook_error'] = str(exc)

    if payload['changed'] and args.on_change_cmd:
        env = dict(os.environ)
        env['POLICYMESH_DRIFT_STATUS'] = payload['status']
        env['POLICYMESH_DRIFT_PREVIOUS_STATUS'] = previous_status or ''
        env['POLICYMESH_DRIFT_CHANGED'] = 'true'
        env['POLICYMESH_DRIFT_PAYLOAD'] = json.dumps(payload, sort_keys=True)
        completed = subprocess.run(args.on_change_cmd, shell=True, env=env, check=False)
        payload['change_hook_exit_code'] = completed.returncode

    print(json.dumps(payload, indent=2))
    print(f'Wrote {out}')
    return 1 if payload['drift'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
