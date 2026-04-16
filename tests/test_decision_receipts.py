from __future__ import annotations

from datetime import datetime, timezone, timedelta

from nacl.signing import SigningKey

from links.decision_receipts import (
    PolicyDecisionReceipt,
    ReceiptEvidence,
    build_policy_decision_receipt,
    evaluate_policy_update,
    sign_receipt,
    verify_receipt,
)
from links.policy_updates import build_update


def test_receipt_roundtrip_signature_verification():
    update = build_update(
        village_id="ops",
        actor="alice",
        policy={"visibility": "village", "rate_limit_per_min": 20},
        lifecycle_state="active",
        policy_version_id="v1",
    )
    receipt = build_policy_decision_receipt(
        village_id="ops",
        update=update,
        decision="apply",
        reason_codes=["ready_for_apply"],
        notes=["Policy update passed the current admission checks."],
        actor="pull",
        evidence=ReceiptEvidence(selected_source="remote"),
    )
    sk = SigningKey.generate()
    signed = sign_receipt(receipt, sk)
    assert verify_receipt(signed) is True
    broken = PolicyDecisionReceipt.model_validate({**signed.model_dump(mode="json"), "decision": "reject"})
    assert verify_receipt(broken) is False


def test_evaluate_policy_update_defer_on_future_activation():
    update = build_update(
        village_id="ops",
        actor="alice",
        policy={"visibility": "village"},
        lifecycle_state="approved",
        activation_time=(datetime.now(timezone.utc) + timedelta(hours=3)).isoformat().replace("+00:00", "Z"),
        quorum_metadata={"model": "m_of_n", "threshold_m": 2},
    )
    decision, reason_codes, notes = evaluate_policy_update(
        {"require_quorum_metadata": True},
        update,
        manifest_ok=True,
        signer_ok=True,
    )
    assert decision == "defer"
    assert "awaiting_activation_time" in reason_codes
    assert notes


def test_evaluate_policy_update_reject_without_required_quorum_metadata():
    update = build_update(
        village_id="ops",
        actor="alice",
        policy={"visibility": "village"},
        lifecycle_state="active",
    )
    decision, reason_codes, notes = evaluate_policy_update(
        {"require_quorum_metadata": True},
        update,
        manifest_ok=False,
        signer_ok=True,
    )
    assert decision == "reject"
    assert "manifest_untrusted" in reason_codes
    assert "missing_quorum_metadata" in reason_codes
    assert notes
