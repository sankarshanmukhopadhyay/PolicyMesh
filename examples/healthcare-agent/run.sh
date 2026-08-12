#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python examples/healthcare-agent/run.py "${1:-all}"
