#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/../.."
python examples/travel-hospitality/run.py "${1:-permitted-booking}"
