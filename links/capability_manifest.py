"""capability_manifest — machine-readable capability declarations for PolicyMesh nodes.

A capability manifest declares what a node supports so that peers, federation
pilots, and operators can make programmatic decisions about compatibility and
trust without reading docs or probing endpoints.

Design principles
-----------------
- The manifest is a plain JSON artifact.  No live endpoint is required for
  generation; it is written once (or on demand) and served statically or
  over HTTP.
- All fields are optional beyond ``node_id`` and ``generated_at``; a minimal
  manifest is valid and still useful.
- The manifest deliberately separates *stable* from *experimental* surfaces so
  consumers do not need to infer maturity from version numbers.

Typical usage
-------------
    from links.capability_manifest import build_manifest, write_manifest

    manifest = build_manifest(
        node_id="node.example.org",
        storage_mode="sqlite",
        reconciliation_mode="lineage_aware",
        transparency_features=["http_publish", "signed_checkpoint"],
    )
    write_manifest(Path("artifacts/capability_manifest.json"), manifest)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STABLE_FEATURES = frozenset(
    {
        "claim_bundles",
        "village_policy",
        "quorum_m_of_n",
        "policy_feed_pull",
        "drift_detection",
        "transparency_checkpoints",
        "audit_log",
        "quarantine_workflow",
        "storage_filesystem",
        "storage_sqlite",
        "reconciliation_lineage_aware",
        "policy_rollback",
        "policy_decision_receipts",
        "policy_lifecycle",
        "policy_diff",
        "trust_anchor_registry",
        "replay_protection",
        "issuer_allowlist",
    }
)

EXPERIMENTAL_FEATURES = frozenset(
    {
        "quorum_weighted",
        "quorum_role_based",
        "checkpoint_http_publish",
        "checkpoint_signed_digest",
        "checkpoint_peer_compare",
        "capability_manifest",
        "drift_class_taxonomy",
        "federation_comparison",
    }
)

_STORAGE_MODES = ("filesystem", "sqlite")
_RECONCILIATION_MODES = ("latest_wins", "lineage_aware")


# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------

MANIFEST_SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_manifest(
    *,
    node_id: str,
    storage_mode: str = "filesystem",
    reconciliation_mode: str = "lineage_aware",
    transparency_features: list[str] | None = None,
    experimental_features: list[str] | None = None,
    federation_pilot: bool = False,
    operator_notes: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a capability manifest dict for this node.

    Parameters
    ----------
    node_id:
        A stable, human-readable identifier for the node (e.g. hostname or
        org-scoped name).  Not required to be globally unique.
    storage_mode:
        ``"filesystem"`` (default) or ``"sqlite"``.
    reconciliation_mode:
        ``"lineage_aware"`` (default) or ``"latest_wins"``.
    transparency_features:
        List of transparency capability tokens.  Any subset of
        ``{"http_publish", "signed_checkpoint", "peer_compare"}``.
    experimental_features:
        Explicit list of experimental surface tokens that this node is
        running.  Peers should treat these surfaces as non-stable.
    federation_pilot:
        Set to ``True`` when this node is participating in a small-federation
        pilot and has accepted the operator acceptance criteria.
    operator_notes:
        Free-text notes for human readers (not parsed by consumers).
    extra:
        Any additional vendor or deployment metadata.  Merged at the top level
        of the manifest under the key ``"extensions"``.
    """
    if storage_mode not in _STORAGE_MODES:
        raise ValueError(
            f"storage_mode must be one of {_STORAGE_MODES!r}, got {storage_mode!r}"
        )
    if reconciliation_mode not in _RECONCILIATION_MODES:
        raise ValueError(
            f"reconciliation_mode must be one of {_RECONCILIATION_MODES!r}, "
            f"got {reconciliation_mode!r}"
        )

    transparency_features = list(transparency_features or [])
    experimental_features = list(experimental_features or [])

    # Derive feature list from stable set + transparency tokens
    stable = list(
        STABLE_FEATURES
        & {
            "claim_bundles",
            "village_policy",
            "quorum_m_of_n",
            "policy_feed_pull",
            "drift_detection",
            "transparency_checkpoints",
            "audit_log",
            "quarantine_workflow",
            "policy_rollback",
        "policy_decision_receipts",
            "policy_decision_receipts",
            "policy_lifecycle",
            "policy_diff",
            "trust_anchor_registry",
            "replay_protection",
            "issuer_allowlist",
            f"storage_{storage_mode}",
            f"reconciliation_{reconciliation_mode}",
        }
    )

    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "node_id": node_id,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "storage_mode": storage_mode,
        "reconciliation_mode": reconciliation_mode,
        "transparency_features": sorted(transparency_features),
        "stable_features": sorted(stable),
        "experimental_features": sorted(experimental_features),
        "federation_pilot": federation_pilot,
    }

    if operator_notes:
        manifest["operator_notes"] = operator_notes
    if extra:
        manifest["extensions"] = extra

    manifest["manifest_hash"] = _hash_manifest_body(manifest)
    return manifest


def write_manifest(path: Path, manifest: dict[str, Any]) -> Path:
    """Write *manifest* as indented JSON to *path*.

    Parent directories are created as needed.  Returns the resolved path.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return path.resolve()


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and return a capability manifest from *path*."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_manifest_hash(manifest: dict[str, Any]) -> tuple[bool, str]:
    """Verify the embedded ``manifest_hash`` matches the manifest body.

    Returns ``(True, "ok")`` or ``(False, reason)``.
    """
    stored = manifest.get("manifest_hash")
    if not stored:
        return False, "manifest_hash field missing"
    body = {k: v for k, v in manifest.items() if k != "manifest_hash"}
    expected = _hash_manifest_body(body)
    if stored != expected:
        return False, f"hash mismatch: stored={stored!r}, expected={expected!r}"
    return True, "ok"


def check_compatibility(
    local: dict[str, Any],
    peer: dict[str, Any],
    *,
    require_storage_match: bool = False,
) -> dict[str, Any]:
    """Compare two capability manifests and return a compatibility report.

    The report has the following shape::

        {
            "compatible": bool,
            "shared_stable_features": [...],
            "local_only_features": [...],
            "peer_only_features": [...],
            "shared_transparency_features": [...],
            "storage_match": bool,
            "reconciliation_match": bool,
            "notes": [str, ...],
        }
    """
    local_stable = set(local.get("stable_features", []))
    peer_stable = set(peer.get("stable_features", []))
    local_trans = set(local.get("transparency_features", []))
    peer_trans = set(peer.get("transparency_features", []))

    storage_match = local.get("storage_mode") == peer.get("storage_mode")
    reconciliation_match = (
        local.get("reconciliation_mode") == peer.get("reconciliation_mode")
    )

    notes: list[str] = []
    compatible = True

    if require_storage_match and not storage_match:
        compatible = False
        notes.append(
            f"storage_mode mismatch: local={local.get('storage_mode')!r}, "
            f"peer={peer.get('storage_mode')!r}"
        )

    if not reconciliation_match:
        notes.append(
            f"reconciliation_mode differs: local={local.get('reconciliation_mode')!r}, "
            f"peer={peer.get('reconciliation_mode')!r}; lineage_aware is recommended for both"
        )

    if peer.get("federation_pilot") and not local.get("federation_pilot"):
        notes.append(
            "peer is in federation_pilot mode but local node is not; "
            "review acceptance criteria before exchanging checkpoints"
        )

    return {
        "compatible": compatible,
        "shared_stable_features": sorted(local_stable & peer_stable),
        "local_only_features": sorted(local_stable - peer_stable),
        "peer_only_features": sorted(peer_stable - local_stable),
        "shared_transparency_features": sorted(local_trans & peer_trans),
        "storage_match": storage_match,
        "reconciliation_match": reconciliation_match,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _hash_manifest_body(body: dict[str, Any]) -> str:
    """Return a SHA-256 hex digest of the canonical JSON body."""
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
