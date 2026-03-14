#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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

    payload = {
        'village_id': args.village_id,
        'checked_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'local_policy_hash': local_hash,
        'remote_policy_hash': remote_hash,
        'drift': local_hash != remote_hash,
        'status': 'drift' if local_hash != remote_hash else 'aligned',
        'source_url': base,
    }

    out = Path(args.out) if args.out else Path('artifacts/drift') / args.village_id / f"drift.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + '
', encoding='utf-8')
    print(json.dumps(payload, indent=2))
    print(f'Wrote {out}')
    return 1 if payload['drift'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
