#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python examples/insurance-claim-agent/run.py "${1:-all}"
