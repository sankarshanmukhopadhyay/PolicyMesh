from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from .file_lock import locked_open
from .validate import validate_village_id

from .audit import write_audit, AuditEvent, policy_hash
from .transparency import append_transparency_entry
from .storage_backend import sqlite_enabled, transaction, write_policy_apply_event
from .keys import load_signing_key_from_env

# Default store root for audit events
store_root = Path("data/store")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class VillageCapabilities(BaseModel):
    can_pull: bool = True
    can_push: bool = False
    can_manage: bool = False


class VillagePolicy(BaseModel):
    visibility: str = Field(default="village", description="private|village|public")
    allowed_predicates: list[str] = Field(default_factory=lambda: ["links.weighted_to"])
    max_window_days: int = 30
    min_signature_alg: str = "Ed25519"
    allow_unverified: bool = False
    retention_days: int = 90
    rate_limit_per_min: int = 60
    rate_limit_strategy: str = Field(default="fixed_window", description="fixed_window|token_bucket")
    submission_quota_per_day: int = Field(default=0, description="0 means unlimited")
    public_policy_endpoint: bool = Field(default=False, description="If true, allow unauthenticated read-only policy endpoint")
    policy_update_expires_minutes: int = Field(default=0, description="0 means no expiry enforcement; otherwise updates must have expires_at within this window")

    # Governance hardening
    issuer_allowlist: list[str] = Field(default_factory=list, description="Allowed issuer key hashes (sha256 of public key).")
    issuer_blocklist: list[str] = Field(default_factory=list, description="Blocked issuer key hashes.")
    issuer_id_allowlist: list[str] = Field(default_factory=list, description="Allowed issuer IDs (bundle.issuer).")
    issuer_id_blocklist: list[str] = Field(default_factory=list, description="Blocked issuer IDs (bundle.issuer).")
    require_policy_signature: bool = False
    policy_signer_allowlist: list[str] = Field(default_factory=list, description="Allowed policy signer key hashes.")
    policy_signature_threshold_m: int = Field(default=1, description="M in M-of-N signer quorum.")
    # Next-gen quorum models (optional)
    policy_quorum: dict = Field(default_factory=dict, description="Quorum config: {model: m_of_n|weighted|role_based, threshold_m, threshold_weight, role_requirements[]}")
    policy_signer_weights: dict[str, float] = Field(default_factory=dict, description="Key-hash -> weight for weighted quorum")
    policy_signer_roles: dict[str, list[str]] = Field(default_factory=dict, description="Key-hash -> roles for role-based quorum")
    require_quorum_metadata: bool = Field(default=False, description="If true, policy update artifacts must include quorum metadata.")
    require_issuer_allowlist: bool = False

    # Role permissions
    capabilities: dict[str, VillageCapabilities] = Field(default_factory=lambda: {
        "observer": VillageCapabilities(can_pull=True, can_push=False, can_manage=False),
        "member":   VillageCapabilities(can_pull=True, can_push=True,  can_manage=False),
        "admin":    VillageCapabilities(can_pull=True, can_push=True,  can_manage=True),
    })


class VillageGovernance(BaseModel):
    admins: list[str] = Field(default_factory=list)
    decision_model: str = "admin-consensus"


class Village(BaseModel):
    village_id: str
    name: str
    description: str = ""
    created_at: datetime
    governance: VillageGovernance
    policy: VillagePolicy


class VillageMember(BaseModel):
    member_id: str
    role: str = "member"  # admin|member|observer
    added_at: datetime
    token_hash: str
    is_revoked: bool = False


def village_dir(root: Path, village_id: str) -> Path:
    validate_village_id(village_id)
    return root / "villages" / village_id


def _members_path(root: Path, village_id: str) -> Path:
    return village_dir(root, village_id) / "members.jsonl"


def _revocations_path(root: Path, village_id: str) -> Path:
    return village_dir(root, village_id) / "revocations.jsonl"


def save_village(root: Path, v: Village) -> Path:
    vd = village_dir(root, v.village_id)
    vd.mkdir(parents=True, exist_ok=True)
    p = vd / "village.json"
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(v.model_dump_json(indent=2), encoding="utf-8")
    tmp.replace(p)
    _members_path(root, v.village_id).touch(exist_ok=True)
    _revocations_path(root, v.village_id).touch(exist_ok=True)
    return p


def load_village(root: Path, village_id: str) -> Village:
    p = village_dir(root, village_id) / "village.json"
    return Village.model_validate_json(p.read_text(encoding="utf-8"))


def save_village_policy(root: Path, village_id: str, policy: VillagePolicy) -> None:
    v = load_village(root, village_id)
    v = v.model_copy(update={"policy": policy})
    save_village(root, v)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def is_token_revoked(root: Path, village_id: str, token_hash: str) -> bool:
    rp = _revocations_path(root, village_id)
    if not rp.exists():
        return False
    with rp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("token_hash") == token_hash:
                return True
    return False


def revoke_token_hash(root: Path, village_id: str, token_hash: str, actor: Optional[str] = None, reason: str = "revoked") -> None:
    rp = _revocations_path(root, village_id)
    rp.parent.mkdir(parents=True, exist_ok=True)
    with locked_open(rp, "a") as f:
        f.write(json.dumps({
            "ts": iso_utc(utc_now()),
            "token_hash": token_hash,
            "actor": actor,
            "reason": reason,
        }, ensure_ascii=False) + "\n")
    write_audit(store_root, AuditEvent(action="member.revoke", village_id=village_id, actor=actor, reason=reason))


def add_member(root: Path, village_id: str, member_id: str, role: str, token_plain: str, actor: Optional[str] = None) -> VillageMember:
    vd = village_dir(root, village_id)
    if not (vd / "village.json").exists():
        raise FileNotFoundError("Village not found")
    m = VillageMember(
        member_id=member_id,
        role=role,
        added_at=utc_now(),
        token_hash=hash_token(token_plain),
        is_revoked=False,
    )
    mp = _members_path(root, village_id)
    with locked_open(mp, "a") as f:
        f.write(json.dumps({
            "member_id": m.member_id,
            "role": m.role,
            "added_at": iso_utc(m.added_at),
            "token_hash": m.token_hash,
            "is_revoked": False,
        }, ensure_ascii=False) + "\n")
    write_audit(store_root, AuditEvent(action="member.add", village_id=village_id, actor=actor, reason=f"role={role}"))
    return m


def list_members(root: Path, village_id: str) -> list[dict]:
    mp = _members_path(root, village_id)
    if not mp.exists():
        return []
    out = []
    with mp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def authorize(root: Path, village_id: str, token_plain: str) -> Optional[dict]:
    """
    Auth: bearer token hashed and matched. Revocations override membership records.
    """
    want = hash_token(token_plain)
    if is_token_revoked(root, village_id, want):
        return None
    for m in list_members(root, village_id):
        if m.get("token_hash") == want and not m.get("is_revoked", False):
            return m
    return None


def revoke_member(root: Path, village_id: str, member_id: str, actor: Optional[str] = None, reason: str = "revoked") -> int:
    """
    Revoke all tokens currently associated with member_id by writing revocations for their token hashes.
    Returns count revoked.
    """
    count = 0
    for m in list_members(root, village_id):
        if m.get("member_id") == member_id:
            th = m.get("token_hash")
            if th and not is_token_revoked(root, village_id, th):
                revoke_token_hash(root, village_id, th, actor=actor, reason=reason)
                count += 1
    return count


def rotate_member_token(root: Path, village_id: str, member_id: str, new_token_plain: str, actor: Optional[str] = None) -> None:
    # revoke existing tokens
    revoke_member(root, village_id, member_id, actor=actor, reason="rotated")
    # add new token with same role as latest record
    role = "member"
    for m in reversed(list_members(root, village_id)):
        if m.get("member_id") == member_id:
            role = m.get("role", "member")
            break
    add_member(root, village_id, member_id, role=role, token_plain=new_token_plain, actor=actor)
    write_audit(store_root, AuditEvent(action="member.rotate", village_id=village_id, actor=actor, reason=f"member_id={member_id}"))


def issuer_key_hash_from_public_key_b64(public_key_b64: str) -> str:
    import base64
    pk = base64.b64decode(public_key_b64)
    return hashlib.sha256(pk).hexdigest()


def issuer_allowed(policy: VillagePolicy, issuer_key_hash: str) -> bool:
    if issuer_key_hash in set(policy.issuer_blocklist):
        return False
    if policy.require_issuer_allowlist:
        return issuer_key_hash in set(policy.issuer_allowlist)
    if policy.issuer_allowlist:
        return issuer_key_hash in set(policy.issuer_allowlist)
    return True


def add_issuer_allow(root: Path, village_id: str, issuer_key_hash: str, actor: Optional[str] = None) -> None:
    v = load_village(root, village_id)
    if issuer_key_hash not in v.policy.issuer_allowlist:
        v.policy.issuer_allowlist.append(issuer_key_hash)
    if issuer_key_hash in v.policy.issuer_blocklist:
        v.policy.issuer_blocklist.remove(issuer_key_hash)
    save_village(root, v)
    write_audit(store_root, AuditEvent(action="issuer.allow", village_id=village_id, actor=actor, issuer_key_hash=issuer_key_hash, policy_hash=policy_hash(v.policy.model_dump())))


def add_issuer_block(root: Path, village_id: str, issuer_key_hash: str, actor: Optional[str] = None) -> None:
    v = load_village(root, village_id)
    if issuer_key_hash not in v.policy.issuer_blocklist:
        v.policy.issuer_blocklist.append(issuer_key_hash)
    save_village(root, v)
    write_audit(store_root, AuditEvent(action="issuer.block", village_id=village_id, actor=actor, issuer_key_hash=issuer_key_hash, policy_hash=policy_hash(v.policy.model_dump())))


def enforce_policy_on_bundle(village: Village, bundle: dict) -> tuple[bool, str]:
    # window guard
    window = int(bundle.get("window_days", 0))
    if window > village.policy.max_window_days:
        return False, f"bundle window_days={window} exceeds max_window_days={village.policy.max_window_days}"
    # predicate allowlist
    allowed = set(village.policy.allowed_predicates)
    for c in bundle.get("claims", []):
        pred = c.get("predicate")
        if pred and pred not in allowed:
            return False, f"predicate '{pred}' not allowed"
    return True, "ok"


def role_can(policy: VillagePolicy, role: str, action: str) -> bool:
    cap = policy.capabilities.get(role) or policy.capabilities.get("observer")
    if action == "pull":
        return bool(cap.can_pull)
    if action == "push":
        return bool(cap.can_push)
    if action == "manage":
        return bool(cap.can_manage)
    return False


def issuer_id_allowed(policy: VillagePolicy, issuer_id: str) -> bool:
    if issuer_id in set(policy.issuer_id_blocklist):
        return False
    if policy.issuer_id_allowlist:
        return issuer_id in set(policy.issuer_id_allowlist)
    return True


def policy_history_path(root: Path, village_id: str) -> Path:
    return village_dir(root, village_id) / "policy_history.jsonl"


def append_policy_history(root: Path, village_id: str, update_obj: dict) -> None:
    p = policy_history_path(root, village_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch(exist_ok=True)
    with locked_open(p, "a") as f:
        f.write(json.dumps(update_obj, ensure_ascii=False) + "\n")


def apply_policy_update(root: Path, village_id: str, policy_obj: dict, actor: Optional[str] = None, update_meta: Optional[dict] = None) -> None:
    v = load_village(root, village_id)
    incoming = VillagePolicy.model_validate(policy_obj)
    v = v.model_copy(update={"policy": incoming})
    save_village(root, v)
    if update_meta is None:
        update_meta = {"actor": actor, "ts": iso_utc(utc_now())}
    applied_at = update_meta.get("ts") if isinstance(update_meta, dict) and update_meta.get("ts") else iso_utc(utc_now())
    history_row = {"policy": incoming.model_dump(), **(update_meta or {})}
    append_policy_history(root, village_id, history_row)

    audit_row = {
        "ts": applied_at,
        "action": "policy.apply",
        "bundle_id": None,
        "village_id": village_id,
        "issuer_key_hash": None,
        "actor": actor,
        "reason": (update_meta or {}).get("policy_update") if isinstance(update_meta, dict) else None,
        "policy_hash": policy_hash(incoming.model_dump()),
    }
    write_audit(store_root, AuditEvent(action="policy.apply", village_id=village_id, actor=actor, reason=audit_row["reason"], policy_hash=audit_row["policy_hash"]))

    transparency_entry = None
    try:
        sk = load_signing_key_from_env()
        transparency_entry = append_transparency_entry(store_root, village_id, policy_hash(incoming.model_dump()), update_meta.get('policy_hash') if isinstance(update_meta, dict) else None, sk)
    except Exception:
        transparency_entry = None

    if sqlite_enabled():
        with transaction(store_root) as conn:
            write_policy_apply_event(
                conn,
                village_id=village_id,
                applied_at=applied_at,
                policy_hash=policy_hash(incoming.model_dump()),
                policy_obj=incoming.model_dump(),
                actor=actor,
                update_hash=(update_meta or {}).get("policy_hash") if isinstance(update_meta, dict) else None,
                history_row=history_row,
            )
