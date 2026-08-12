#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python examples/personal-shopping/run.py "${1:-all}"
