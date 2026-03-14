from __future__ import annotations

import base64
from datetime import datetime
from typing import Optional, List, Dict, Set, Tuple, Any

from pydantic import BaseModel, Field, ConfigDict, model_validator, computed_field
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError

from .utils import canonical_json, sha256_hex, utc_now


def compute_policy_hash(policy: dict) -> str:
    return sha256_hex(canonical_json(policy))


def key_hash_from_public_key_b64(public_key_b64: str) -> str:
    return sha256_hex(base64.b64decode(public_key_b64))


class SignatureEntry(BaseModel):
    public_key: str
    signature: str
    alg: str = 'ed25519'


class QuorumRequirement(BaseModel):
    role: str
    min_signers: int


class QuorumMetadata(BaseModel):
    model: str = Field(description='For example: m_of_n | weighted | role_based')
    threshold_m: Optional[int] = None
    required_weight: Optional[float] = None
    requirements: List[QuorumRequirement] = Field(default_factory=list)


class PolicyChangeSummary(BaseModel):
    added: List[str] = Field(default_factory=list, description='JSON pointer paths added')
    removed: List[str] = Field(default_factory=list, description='JSON pointer paths removed')
    changed: List[str] = Field(default_factory=list, description='JSON pointer paths changed')


class VillagePolicyUpdate(BaseModel):
    """A signed policy update artifact.

    Backwards compatibility:
      - legacy single signature fields: public_key + signature
      - multisig quorum via signatures[]
      - accepts historical `quorum_metadata` aliasing for `quorum`
      - accepts string activation_time and dict-based change_summary inputs
    """

    model_config = ConfigDict(populate_by_name=True)

    village_id: str
    created_at: datetime
    actor: Optional[str] = None
    expires_at: Optional[datetime] = Field(default=None, description='If set, the update must not be applied after this time')

    policy: dict = Field(default_factory=dict)
    policy_hash: str
    policy_version_id: Optional[str] = None
    lifecycle_state: str = Field(default='proposal', description='proposal|approved|active|rolled_back')
    previous_policy_hash: Optional[str] = None
    rollback_to_policy_hash: Optional[str] = None
    activation_time: Optional[datetime] = None
    activation_height: Optional[int] = None
    quorum: Optional[QuorumMetadata] = Field(default=None, validation_alias='quorum_metadata')
    change_summary: Optional[PolicyChangeSummary] = None
    signature_alg: str = 'Ed25519'
    public_key: Optional[str] = None
    signature: Optional[str] = None
    signatures: List[SignatureEntry] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def _compat_inputs(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        if out.get('quorum') is None and out.get('quorum_metadata') is not None:
            out['quorum'] = out.get('quorum_metadata')
        return out

    @computed_field(return_type=Optional[QuorumMetadata])
    @property
    def quorum_metadata(self) -> Optional[QuorumMetadata]:
        return self.quorum


def payload_for_signing(u: VillagePolicyUpdate) -> dict:
    d = u.model_dump()
    d.pop('quorum_metadata', None)
    d.pop('signature', None)
    d.pop('public_key', None)
    d.pop('signatures', None)
    return d


def compute_update_hash(u: VillagePolicyUpdate) -> str:
    return sha256_hex(canonical_json(payload_for_signing(u)))


def build_update(
    village_id: str,
    policy: dict,
    actor: Optional[str] = None,
    *,
    lifecycle_state: str = 'proposal',
    previous_policy_hash: Optional[str] = None,
    activation_time: Optional[datetime | str] = None,
    activation_height: Optional[int] = None,
    policy_version_id: Optional[str] = None,
    quorum: Optional[QuorumMetadata | Dict[str, Any]] = None,
    quorum_metadata: Optional[QuorumMetadata | Dict[str, Any]] = None,
    change_summary: Optional[PolicyChangeSummary | Dict[str, Any]] = None,
) -> VillagePolicyUpdate:
    ph = compute_policy_hash(policy)
    q = quorum if quorum is not None else quorum_metadata
    if isinstance(q, dict):
        q = QuorumMetadata.model_validate(q)
    if isinstance(change_summary, dict):
        change_summary = PolicyChangeSummary.model_validate(change_summary)
    if isinstance(activation_time, str):
        activation_time = datetime.fromisoformat(activation_time.replace('Z', '+00:00'))
    return VillagePolicyUpdate(
        village_id=village_id,
        created_at=utc_now(),
        actor=actor,
        policy=policy,
        policy_hash=ph,
        policy_version_id=policy_version_id or ph,
        lifecycle_state=lifecycle_state,
        previous_policy_hash=previous_policy_hash,
        activation_time=activation_time,
        activation_height=activation_height,
        quorum=q,
        change_summary=change_summary,
    )


def sign_update_legacy(u: VillagePolicyUpdate, signing_key: SigningKey) -> VillagePolicyUpdate:
    payload = payload_for_signing(u)
    sig = signing_key.sign(canonical_json(payload)).signature
    pub = signing_key.verify_key.encode()
    return u.model_copy(update={
        'public_key': base64.b64encode(pub).decode('utf-8'),
        'signature': base64.b64encode(sig).decode('utf-8'),
    })


def add_signature(u: VillagePolicyUpdate, signing_key: SigningKey) -> VillagePolicyUpdate:
    payload = payload_for_signing(u)
    sig = signing_key.sign(canonical_json(payload)).signature
    pub = signing_key.verify_key.encode()
    entry = SignatureEntry(
        public_key=base64.b64encode(pub).decode('utf-8'),
        signature=base64.b64encode(sig).decode('utf-8'),
    )

    seen: Set[str] = set()
    out: List[SignatureEntry] = []
    for e in (u.signatures or []):
        h = key_hash_from_public_key_b64(e.public_key)
        if h in seen:
            continue
        seen.add(h)
        out.append(e)

    h_new = key_hash_from_public_key_b64(entry.public_key)
    if h_new not in seen:
        out.append(entry)

    return u.model_copy(update={'signatures': out})


def _verify_one(payload: dict, public_key_b64: str, signature_b64: str, alg: str = 'ed25519') -> bool:
    if (alg or 'ed25519').lower() != 'ed25519':
        return False
    vk = VerifyKey(base64.b64decode(public_key_b64))
    try:
        vk.verify(canonical_json(payload), base64.b64decode(signature_b64))
        return True
    except (BadSignatureError, ValueError, TypeError):
        return False


def verify_update_any(u: VillagePolicyUpdate) -> bool:
    if u.policy_hash != compute_policy_hash(u.policy):
        return False
    payload = payload_for_signing(u)

    for e in (u.signatures or []):
        if _verify_one(payload, e.public_key, e.signature, getattr(e, 'alg', 'ed25519')):
            return True

    if u.public_key and u.signature:
        return _verify_one(payload, u.public_key, u.signature, 'ed25519')

    return False


def verify_update_quorum(
    u: VillagePolicyUpdate,
    required_m: int,
    signer_allowlist: list[str] | None = None
) -> tuple[bool, str]:
    if required_m < 1:
        return False, 'invalid quorum threshold'
    if u.policy_hash != compute_policy_hash(u.policy):
        return False, 'policy_hash mismatch'

    payload = payload_for_signing(u)
    allow = set(signer_allowlist or [])
    valid_signers: Set[str] = set()

    for e in (u.signatures or []):
        kh = key_hash_from_public_key_b64(e.public_key)
        if allow and kh not in allow:
            continue
        if _verify_one(payload, e.public_key, e.signature, getattr(e, 'alg', 'ed25519')):
            valid_signers.add(kh)

    if u.public_key and u.signature:
        kh = key_hash_from_public_key_b64(u.public_key)
        if (not allow) or (kh in allow):
            if _verify_one(payload, u.public_key, u.signature, 'ed25519'):
                valid_signers.add(kh)

    if len(valid_signers) >= required_m:
        return True, 'ok'
    return False, f'quorum not met (valid={len(valid_signers)} required={required_m})'


def verify_update_weighted_quorum(
    u: VillagePolicyUpdate,
    weights_by_key_hash: Dict[str, float],
    required_weight: float,
    signer_allowlist: list[str] | None = None,
) -> Tuple[bool, str, float]:
    if required_weight <= 0:
        return False, 'invalid weight threshold', 0.0
    if u.policy_hash != compute_policy_hash(u.policy):
        return False, 'policy_hash mismatch', 0.0

    payload = payload_for_signing(u)
    allow = set(signer_allowlist or [])
    achieved = 0.0
    counted: Set[str] = set()

    def maybe_count(pub_b64: str, sig_b64: str, alg: str = 'ed25519'):
        nonlocal achieved
        kh = key_hash_from_public_key_b64(pub_b64)
        if kh in counted:
            return
        if allow and kh not in allow:
            return
        if not _verify_one(payload, pub_b64, sig_b64, alg):
            return
        w = float(weights_by_key_hash.get(kh, 0.0))
        achieved += w
        counted.add(kh)

    for e in (u.signatures or []):
        maybe_count(e.public_key, e.signature, getattr(e, 'alg', 'ed25519'))

    if u.public_key and u.signature:
        maybe_count(u.public_key, u.signature, 'ed25519')

    if achieved >= required_weight:
        return True, 'ok', achieved
    return False, f'weighted quorum not met (weight={achieved} required={required_weight})', achieved


def verify_update_role_based_quorum(
    u: VillagePolicyUpdate,
    roles_by_key_hash: Dict[str, List[str]],
    requirements: List[QuorumRequirement],
    signer_allowlist: list[str] | None = None,
) -> Tuple[bool, str, Dict[str, int]]:
    if u.policy_hash != compute_policy_hash(u.policy):
        return False, 'policy_hash mismatch', {}
    payload = payload_for_signing(u)
    allow = set(signer_allowlist or [])

    role_counts: Dict[str, int] = {r.role: 0 for r in requirements}
    counted: Set[str] = set()

    def maybe_count(pub_b64: str, sig_b64: str, alg: str = 'ed25519'):
        kh = key_hash_from_public_key_b64(pub_b64)
        if kh in counted:
            return
        if allow and kh not in allow:
            return
        if not _verify_one(payload, pub_b64, sig_b64, alg):
            return
        counted.add(kh)
        for role in roles_by_key_hash.get(kh, []):
            if role in role_counts:
                role_counts[role] += 1

    for e in (u.signatures or []):
        maybe_count(e.public_key, e.signature, getattr(e, 'alg', 'ed25519'))

    if u.public_key and u.signature:
        maybe_count(u.public_key, u.signature, 'ed25519')

    missing = []
    for req in requirements:
        if role_counts.get(req.role, 0) < int(req.min_signers):
            missing.append(f"{req.role}({role_counts.get(req.role, 0)}/{req.min_signers})")

    if not missing:
        return True, 'ok', role_counts
    return False, 'role quorum not met: ' + ', '.join(missing), role_counts
