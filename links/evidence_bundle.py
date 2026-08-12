from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import json
import shutil

from pydantic import BaseModel, Field


class EvidenceArtifact(BaseModel):
    name: str
    path: str
    sha256: str
    media_type: str = "application/json"


class PolicyEvidenceManifest(BaseModel):
    format: str = "policymesh.evidence.v1"
    event_id: str
    village_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    policy_version: Optional[str] = None
    actor: Optional[str] = None
    authority_context: Optional[dict] = None
    artifacts: List[EvidenceArtifact] = Field(default_factory=list)
    verification_result: str = "assembled"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_evidence_bundle(
    out_root: Path,
    *,
    event_id: str,
    village_id: str,
    sources: List[Path],
    policy_version: Optional[str] = None,
    actor: Optional[str] = None,
    authority_context: Optional[dict] = None,
) -> Path:
    bundle = out_root / village_id / event_id
    bundle.mkdir(parents=True, exist_ok=True)
    artifacts: List[EvidenceArtifact] = []
    for src in sources:
        if not src.exists() or not src.is_file():
            raise FileNotFoundError(src)
        dst = bundle / src.name
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        artifacts.append(EvidenceArtifact(name=src.name, path=src.name, sha256=_sha256(dst)))
    manifest = PolicyEvidenceManifest(
        event_id=event_id,
        village_id=village_id,
        policy_version=policy_version,
        actor=actor,
        authority_context=authority_context,
        artifacts=artifacts,
    )
    manifest_path = bundle / "manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    digest_payload = {"manifest_sha256": _sha256(manifest_path), "artifacts": {a.name: a.sha256 for a in artifacts}}
    (bundle / "evidence-digest.json").write_text(json.dumps(digest_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return bundle


def verify_evidence_bundle(bundle: Path) -> tuple[bool, List[str]]:
    errors: List[str] = []
    manifest_path = bundle / "manifest.json"
    if not manifest_path.exists():
        return False, ["manifest.json missing"]
    manifest = PolicyEvidenceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    for artifact in manifest.artifacts:
        path = bundle / artifact.path
        if not path.exists():
            errors.append(f"missing artifact: {artifact.path}")
        elif _sha256(path) != artifact.sha256:
            errors.append(f"digest mismatch: {artifact.path}")
    return not errors, errors
