from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Iterable
import requests


@dataclass
class LinksClient:
    base_url: str
    token: Optional[str] = None
    timeout: float = 10.0

    def _headers(self) -> Dict[str, str]:
        h: Dict[str, str] = {"accept": "application/json"}
        if self.token:
            h["authorization"] = f"Bearer {self.token}"
        return h

    def latest_policy(self, village_id: str) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/villages/{village_id}/policy/latest", headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def policy_manifest(self, village_id: str) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/villages/{village_id}/policy/manifest", headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def policy_update_by_hash(self, village_id: str, policy_hash: str) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/villages/{village_id}/policy/by_hash/{policy_hash}", headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def transparency_log(self, village_id: str, limit: int = 500) -> Iterable[Dict[str, Any]]:
        r = requests.get(f"{self.base_url}/villages/{village_id}/transparency/policy_log", headers=self._headers(), params={"limit": limit}, timeout=self.timeout, stream=True)
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            import json
            yield json.loads(line)
