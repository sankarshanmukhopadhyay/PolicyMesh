from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Iterable, Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_default(o: Any):
    if isinstance(o, datetime):
        if o.tzinfo is None:
            return o.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')
        return o.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    raise TypeError(f'Object of type {o.__class__.__name__} is not JSON serializable')


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=_json_default).encode('utf-8')


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def summarize(items: Iterable[Any]) -> str:
    items = list(items)
    if not items:
        return 'empty'
    return f"{len(items)} items, first={items[0]}"
