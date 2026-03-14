from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from links.transparency import write_transparency_checkpoint


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/transparency_checkpoint.py <village_id>", file=sys.stderr)
        return 2
    village_id = sys.argv[1]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path("artifacts/transparency") / village_id / f"checkpoint.{stamp}.json"
    write_transparency_checkpoint(Path("data/store"), village_id, out)
    print(json.dumps({"village_id": village_id, "path": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
