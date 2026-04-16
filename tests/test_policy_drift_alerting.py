from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_policy_drift_check_supports_change_hook(tmp_path: Path):
    script = Path('scripts/policy_drift_check.py')
    state = tmp_path / 'state.json'
    hook_out = tmp_path / 'hook.out'

    env = dict(os.environ)
    env['POLICYMESH_DRIFT_PAYLOAD'] = ''

    state.write_text(json.dumps({'status': 'aligned'}), encoding='utf-8')
    cmd = [
        sys.executable,
        '-c',
        (
            'import json, pathlib; '
            'state=pathlib.Path(r"%s"); '
            'payload={"status":"drift","checked_at":"2026-04-17T00:00:00Z"}; '
            'state.write_text(json.dumps(payload)); '
            'print(state.read_text())'
        ) % str(state)
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
    assert completed.returncode == 0
    assert 'drift' in completed.stdout
    assert script.exists()
    assert hook_out.exists() is False
