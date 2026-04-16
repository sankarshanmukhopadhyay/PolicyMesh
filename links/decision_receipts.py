from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey
from pydantic import BaseModel, Field

from .policy_updates import VillagePolicyUpdate, payload_for_signing
from .utils import canonical_json, sha256_hex


RECEIPT_FORMAT = "links.policy.decision_receipt.v1"


class ReceiptEvidence(BaseModel):
    selected_source: Optional[str] = None
    selected_head: Optional[str] = None
    selection_reason: Optional[str] = None
    manifest_ok: Optional[bool] = None
    manifest_message: Optional[str] = None
    reconciliation_status: Optional[str] = None
    reconciliation_report_path: Optional[str] = None
    fetched_parent_hashes: List[str] = Field(default_factory=list)
    unresolved_parent_hashes: List[str] = Field(default_factory=list)
    quorum_summary: Dict[str, Any] = Field(default_factory=dict)


class PolicyDecisionReceipt(BaseModel):
    format: str = RECEIPT_FORMAT
    receipt_id: str
    ts: datetime
    village_id: str
    action: str = Field(description="policy_pull|policy_apply|policy_verify")
    decision: str = Field(description="apply|defer|reject")
    subject_type: str = Field(default="policy_update")
    subject_id: str
    actor: Optional[str] = None
    candidate_policy_hash: str
    local_policy_hash: Optional[str] = None
    policy_version_id: Optional[str] = None
    lifecycle_state: Optional[str] = None
    activation_time: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    reason_codes: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    evidence: ReceiptEvidence = Field(default_factory=ReceiptEvidence)
    signature_alg: Optional[str] = None
    signer_public_key: Optional[str] = None
    signature: Optional[str] = None


def _unsigned_receipt_payload(r: PolicyDecisionReceipt) -> dict:
    d = r.model_dump(mode="json")
    d.pop("receipt_id", None)
    d.pop("signature_alg", None)
    d.pop("signer_public_key", None)
    d.pop("signature", None)
    return d


def compute_receipt_id(payload: dict) -> str:
    return sha256_hex(canonical_json(payload))


def build_policy_decision_receipt(
    *,
    village_id: str,
    update: VillagePolicyUpdate,
    decision: str,
    reason_codes: List[str],
    notes: Optional[List[str]] = None,
    actor: Optional[str] = None,
    action: str = "policy_pull",
    local_policy_hash: Optional[str] = None,
    evidence: Optional[ReceiptEvidence] = None,
    now: Optional[datetime] = None,
) -> PolicyDecisionReceipt:
    ts = now or datetime.now(timezone.utc)
    seed = {
        "format": RECEIPT_FORMAT,
        "ts": ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "village_id": village_id,
        "action": action,
        "decision": decision,
        "subject_type": "policy_update",
        "subject_id": update.policy_hash,
        "actor": actor,
        "candidate_policy_hash": update.policy_hash,
        "local_policy_hash": local_policy_hash,
        "policy_version_id": update.policy_version_id,
        "lifecycle_state": update.lifecycle_state,
        "activation_time": update.activation_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if update.activation_time else None,
        "expires_at": update.expires_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if update.expires_at else None,
        "reason_codes": list(reason_codes),
        "notes": list(notes or []),
        "evidence": (evidence or ReceiptEvidence()).model_dump(mode="json"),
    }
    receipt_id = compute_receipt_id(seed)
    return PolicyDecisionReceipt(
        receipt_id=receipt_id,
        ts=ts,
        village_id=village_id,
        action=action,
        decision=decision,
        subject_id=update.policy_hash,
        actor=actor,
        candidate_policy_hash=update.policy_hash,
        local_policy_hash=local_policy_hash,
        policy_version_id=update.policy_version_id,
        lifecycle_state=update.lifecycle_state,
        activation_time=update.activation_time,
        expires_at=update.expires_at,
        reason_codes=list(reason_codes),
        notes=list(notes or []),
        evidence=evidence or ReceiptEvidence(),
    )


def sign_receipt(receipt: PolicyDecisionReceipt, signing_key: SigningKey) -> PolicyDecisionReceipt:
    payload = _unsigned_receipt_payload(receipt)
    sig = signing_key.sign(canonical_json(payload)).signature
    pub = signing_key.verify_key.encode()
    return receipt.model_copy(update={
        "signature_alg": "Ed25519",
        "signer_public_key": base64.b64encode(pub).decode("utf-8"),
        "signature": base64.b64encode(sig).decode("utf-8"),
    })


def verify_receipt(receipt: PolicyDecisionReceipt) -> bool:
    payload = _unsigned_receipt_payload(receipt)
    if receipt.receipt_id != compute_receipt_id(payload):
        return False
    if not receipt.signer_public_key or not receipt.signature:
        return True
    try:
        vk = VerifyKey(base64.b64decode(receipt.signer_public_key))
        vk.verify(canonical_json(payload), base64.b64decode(receipt.signature))
        return True
    except (BadSignatureError, ValueError, TypeError):
        return False


def write_receipt(out_path: Path, receipt: PolicyDecisionReceipt) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(receipt.model_dump_json(indent=2), encoding="utf-8")
    return out_path


def evaluate_policy_update(
    current_policy: dict,
    update: VillagePolicyUpdate,
    *,
    manifest_ok: Optional[bool] = None,
    signer_ok: bool = True,
    signer_message: str = "ok",
    now: Optional[datetime] = None,
) -> Tuple[str, List[str], List[str]]:
    ts = now or datetime.now(timezone.utc)
    reason_codes: List[str] = []
    notes: List[str] = []

    lifecycle = (update.lifecycle_state or "proposal").lower()
    if manifest_ok is False:
        reason_codes.append("manifest_untrusted")
        notes.append("Remote policy manifest could not be validated against local trust requirements.")
    if not signer_ok:
        reason_codes.append("signer_verification_failed")
        notes.append(signer_message)

    require_quorum_metadata = bool(current_policy.get("require_quorum_metadata", False))
    if require_quorum_metadata and update.quorum is None:
        reason_codes.append("missing_quorum_metadata")
        notes.append("Local village policy requires quorum metadata on incoming policy updates.")

    if update.expires_at and update.expires_at < ts:
        reason_codes.append("update_expired")
        notes.append("Policy update expiry time is in the past.")

    if lifecycle == "proposal":
        reason_codes.append("awaiting_approval")
        notes.append("Lifecycle state is still proposal.")
    elif lifecycle == "rolled_back":
        reason_codes.append("rolled_back_update")
        notes.append("Lifecycle state marks this update as rolled back.")

    if update.activation_time and update.activation_time > ts:
        reason_codes.append("awaiting_activation_time")
        notes.append("Activation time has not yet been reached.")

    blocking = {"manifest_untrusted", "signer_verification_failed", "missing_quorum_metadata", "update_expired", "rolled_back_update"}
    defer_only = {"awaiting_approval", "awaiting_activation_time"}

    if any(code in blocking for code in reason_codes):
        return "reject", reason_codes, notes
    if any(code in defer_only for code in reason_codes):
        return "defer", reason_codes, notes
    return "apply", ["ready_for_apply"], ["Policy update passed the current admission checks."]


def build_quorum_summary(update: VillagePolicyUpdate) -> Dict[str, Any]:
    q = update.quorum
    if q is None:
        return {}
    return q.model_dump(mode="json")
