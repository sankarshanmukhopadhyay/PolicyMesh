from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Optional, Iterable, Tuple, Dict, List, Any
from datetime import timezone, datetime

from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError

from pydantic import BaseModel

from .validate import validate_village_id
from .policy_updates import (
    VillagePolicyUpdate,
    verify_update_any,
    verify_update_quorum,
    verify_update_weighted_quorum,
    verify_update_role_based_quorum,
    compute_update_hash,
    QuorumRequirement,
    canonical_json,
    sha256_hex,
)


def _updates_dir(villages_root: Path, village_id: str) -> Path:
    validate_village_id(village_id)
    d = villages_root / "villages" / village_id / "policy_updates"
    d.mkdir(parents=True, exist_ok=True)
    return d


def store_policy_update(villages_root: Path, u: VillagePolicyUpdate) -> Path:
    d = _updates_dir(villages_root, u.village_id)
    ts = u.created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z").replace(":", "").replace("-", "")
    p = d / f"{ts}.{u.policy_hash}.json"
    p.write_text(u.model_dump_json(indent=2), encoding="utf-8")
    return p


def iter_policy_updates(villages_root: Path, village_id: str) -> Iterable[VillagePolicyUpdate]:
    d = _updates_dir(villages_root, village_id)
    for p in sorted(d.glob("*.json")):
        try:
            yield VillagePolicyUpdate.model_validate_json(p.read_text(encoding="utf-8"))
        except Exception:
            continue


def list_policy_updates(villages_root: Path, village_id: str) -> List[VillagePolicyUpdate]:
    ups = list(iter_policy_updates(villages_root, village_id))
    ups.sort(key=lambda u: (u.created_at, u.policy_hash))
    return ups


def latest_policy_update(villages_root: Path, village_id: str) -> Optional[VillagePolicyUpdate]:
    ups = list_policy_updates(villages_root, village_id)
    if not ups:
        return None
    return sorted(ups, key=lambda u: (u.created_at, u.policy_hash), reverse=True)[0]


def filter_updates_since(villages_root: Path, village_id: str, since_hash: Optional[str]) -> list[VillagePolicyUpdate]:
    ups = list_policy_updates(villages_root, village_id)
    if not since_hash:
        return ups
    out: List[VillagePolicyUpdate] = []
    seen = False
    for u in ups:
        if seen:
            out.append(u)
        if u.policy_hash == since_hash:
            seen = True
    return out


def paginate_updates(ups: List[VillagePolicyUpdate], cursor: Optional[str], limit: int) -> tuple[List[VillagePolicyUpdate], Optional[str]]:
    """Cursor pagination using policy_hash of the last item returned."""
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500

    start_idx = 0
    if cursor:
        for i, u in enumerate(ups):
            if u.policy_hash == cursor:
                start_idx = i + 1
                break

    items = ups[start_idx:start_idx + limit]
    next_cursor = items[-1].policy_hash if (start_idx + limit) < len(ups) and items else None
    return items, next_cursor


# -------------------------------------------------------------------
# Quorum evaluation driven by policy config (supports weighted & roles)
# -------------------------------------------------------------------

def _policy_allowlist(policy: dict) -> list[str]:
    return list(policy.get("policy_signer_allowlist", []) or [])


def manifest_trust_policy(policy: dict) -> dict:
    return {
        "trusted_signer_key_hashes": list(policy.get("trusted_manifest_signer_allowlist", []) or []),
        "require_signature": bool(policy.get("require_manifest_signature", False)),
        "require_trusted_signer": bool(policy.get("require_trusted_manifest_signer", False)),
    }


def evaluate_policy_quorum(policy: dict, u: VillagePolicyUpdate) -> tuple[bool, str]:
    """Enforce policy signature rules with optional quorum models.

    Policy config (backwards compatible):
      - require_policy_signature: bool
      - policy_signer_allowlist: [key_hash]
      - policy_signature_threshold_m: int

    New (preferred):
      - policy_quorum: {model, threshold_m, threshold_weight, role_requirements[]}
      - policy_signer_weights: {key_hash: weight}
      - policy_signer_roles: {key_hash: [roles]}

    Returns (ok, msg).
    """
    require_sig = bool(policy.get("require_policy_signature", False))
    allowlist = _policy_allowlist(policy)

    quorum_cfg = policy.get("policy_quorum") or {}
    model = str(quorum_cfg.get("model") or "m_of_n")

    if require_sig:
        # Encourage explicit quorum metadata for audit clarity (non-fatal if missing)
        # If operators want strictness, they can require it in their review process.
        if model == "weighted":
            weights = {str(k): float(v) for k, v in (policy.get("policy_signer_weights") or {}).items()}
            required_weight = float(quorum_cfg.get("threshold_weight") or 0.0)
            ok, msg, _ = verify_update_weighted_quorum(u, weights_by_key_hash=weights, required_weight=required_weight, signer_allowlist=allowlist if allowlist else None)
            return ok, msg

        if model == "role_based":
            roles_map = {str(k): list(v) for k, v in (policy.get("policy_signer_roles") or {}).items()}
            reqs = [QuorumRequirement.model_validate(r) for r in (quorum_cfg.get("role_requirements") or [])]
            ok, msg, _ = verify_update_role_based_quorum(u, roles_by_key_hash=roles_map, requirements=reqs, signer_allowlist=allowlist if allowlist else None)
            return ok, msg

        # default: m_of_n
        threshold_m = int(quorum_cfg.get("threshold_m") or policy.get("policy_signature_threshold_m") or 1)
        ok, msg = verify_update_quorum(u, required_m=threshold_m, signer_allowlist=allowlist if allowlist else None)
        return ok, msg

    # signatures optional: if any signature material exists, require at least one valid signature
    has_any = bool(u.signatures) or bool(u.public_key) or bool(u.signature)
    if has_any:
        if allowlist:
            ok, msg = verify_update_quorum(u, required_m=1, signer_allowlist=allowlist)
            return ok, msg
        if not verify_update_any(u):
            return False, "signature invalid"

    return True, "ok"


def signer_allowed(policy: dict, u: VillagePolicyUpdate) -> Tuple[bool, str]:
    """Compatibility wrapper (kept for older call sites)."""
    return evaluate_policy_quorum(policy, u)


# -------------------------------------------------------------------
# Feed manifest + integrity metadata
# -------------------------------------------------------------------

def _merkle_root(items: List[str]) -> str:
    """Compute a simple merkle root over hex hashes (sha256)."""
    if not items:
        return sha256_hex(b"")
    layer = [bytes.fromhex(h) for h in items]
    while len(layer) > 1:
        nxt: List[bytes] = []
        for i in range(0, len(layer), 2):
            left = layer[i]
            right = layer[i + 1] if (i + 1) < len(layer) else layer[i]
            nxt.append(hashlib.sha256(left + right).digest())
        layer = nxt
    return layer[0].hex()


class PolicyFeedManifest(BaseModel):
    village_id: str
    generated_at: datetime
    head_policy_hash: Optional[str] = None
    count: int = 0

    merkle_root: str
    chain_head: str

    # update summaries in chronological order
    items: List[Dict[str, Any]] = []

    # signature over canonical_json(payload_for_signing(manifest))
    signature_alg: str = "Ed25519"
    signer_public_key: Optional[str] = None  # base64
    signature: Optional[str] = None          # base64


def _manifest_payload(m: PolicyFeedManifest) -> dict:
    d = m.model_dump()
    d.pop("signature", None)
    d.pop("signer_public_key", None)
    return d


def sign_manifest(m: PolicyFeedManifest, signing_key: SigningKey) -> PolicyFeedManifest:
    payload = _manifest_payload(m)
    sig = signing_key.sign(canonical_json(payload)).signature
    pub = signing_key.verify_key.encode()
    return m.model_copy(update={
        "signer_public_key": base64.b64encode(pub).decode("utf-8"),
        "signature": base64.b64encode(sig).decode("utf-8"),
    })


def verify_manifest(m: PolicyFeedManifest, trusted_signer_key_hashes: Optional[List[str]] = None) -> tuple[bool, str]:
    if not (m.signer_public_key and m.signature):
        return False, "unsigned manifest"
    kh = hashlib.sha256(base64.b64decode(m.signer_public_key)).hexdigest()
    if trusted_signer_key_hashes and kh not in set(trusted_signer_key_hashes):
        return False, "manifest signer not trusted"

    payload = _manifest_payload(m)
    vk = VerifyKey(base64.b64decode(m.signer_public_key))
    try:
        vk.verify(canonical_json(payload), base64.b64decode(m.signature))
    except BadSignatureError:
        return False, "manifest signature invalid"

    return True, "ok"


def verify_manifest_against_policy(policy: dict, m: PolicyFeedManifest) -> tuple[bool, str]:
    trust = manifest_trust_policy(policy)
    trusted = trust["trusted_signer_key_hashes"]
    require_signature = trust["require_signature"]
    require_trusted = trust["require_trusted_signer"]

    if not (m.signer_public_key and m.signature):
        if require_signature or require_trusted:
            return False, "unsigned manifest rejected by policy"
        return True, "unsigned manifest accepted for development use"

    signer_hash = hashlib.sha256(base64.b64decode(m.signer_public_key)).hexdigest()
    ok, msg = verify_manifest(m)
    if not ok:
        return False, msg
    if require_trusted and trusted and signer_hash not in set(trusted):
        return False, "manifest signer not trusted"
    if trusted and signer_hash in set(trusted):
        return True, f"manifest signature verified by trusted signer {signer_hash}"
    return True, f"manifest signature verified by unpinned signer {signer_hash}"


def get_policy_update_by_hash(villages_root: Path, village_id: str, policy_hash: str) -> Optional[VillagePolicyUpdate]:
    for u in iter_policy_updates(villages_root, village_id):
        if u.policy_hash == policy_hash:
            return u
    return None


def fill_history_gaps(
    initial_updates: List[VillagePolicyUpdate],
    known_policy_hashes: Optional[set[str]] = None,
    fetch_update_by_hash=None,
    max_fetch: int = 500,
) -> tuple[List[VillagePolicyUpdate], List[str], List[str]]:
    """Resolve parent-chain gaps by fetching missing ancestors one by one.

    Returns (combined_updates, fetched_hashes, unresolved_parent_hashes).
    """
    updates_by_hash = {u.policy_hash: u for u in initial_updates}
    known = set(known_policy_hashes or set()) | set(updates_by_hash.keys())
    fetched: List[str] = []
    unresolved: List[str] = []

    pending = [u.previous_policy_hash for u in updates_by_hash.values() if u.previous_policy_hash and u.previous_policy_hash not in known]
    seen_pending: set[str] = set()

    while pending and len(fetched) < max_fetch:
        wanted = pending.pop(0)
        if not wanted or wanted in known or wanted in seen_pending:
            continue
        seen_pending.add(wanted)
        if fetch_update_by_hash is None:
            unresolved.append(wanted)
            continue
        fetched_update = fetch_update_by_hash(wanted)
        if fetched_update is None:
            unresolved.append(wanted)
            continue
        updates_by_hash[fetched_update.policy_hash] = fetched_update
        known.add(fetched_update.policy_hash)
        fetched.append(fetched_update.policy_hash)
        prev = fetched_update.previous_policy_hash
        if prev and prev not in known:
            pending.append(prev)

    while pending:
        wanted = pending.pop(0)
        if wanted and wanted not in known and wanted not in unresolved:
            unresolved.append(wanted)

    combined = sorted(updates_by_hash.values(), key=lambda u: (u.created_at, u.policy_hash))
    return combined, fetched, unresolved


def build_policy_feed_manifest(villages_root: Path, village_id: str) -> PolicyFeedManifest:
    ups = list_policy_updates(villages_root, village_id)
    item_hashes: List[str] = []
    chain_prev = "0" * 64
    items: List[Dict[str, Any]] = []
    for u in ups:
        uh = compute_update_hash(u)
        item_hashes.append(uh)
        chain_prev = sha256_hex(bytes.fromhex(chain_prev) + bytes.fromhex(uh))
        items.append({
            "created_at": u.created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "policy_hash": u.policy_hash,
            "update_hash": uh,
            "previous_policy_hash": u.previous_policy_hash,
            "lifecycle_state": u.lifecycle_state,
            "activation_time": u.activation_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if u.activation_time else None,
            "activation_height": u.activation_height,
        })

    head = ups[-1].policy_hash if ups else None
    m = PolicyFeedManifest(
        village_id=village_id,
        generated_at=datetime.now(timezone.utc),
        head_policy_hash=head,
        count=len(ups),
        merkle_root=_merkle_root(item_hashes),
        chain_head=chain_prev,
        items=items,
    )
    return m
