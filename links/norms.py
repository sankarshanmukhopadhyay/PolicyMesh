from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from pydantic import BaseModel, Field, ConfigDict, model_validator

from .utils import canonical_json, sha256_hex, utc_now
from .villages import VillagePolicy, apply_policy_update
from .policy_updates import build_update, VillagePolicyUpdate

SUPPORTED_CATEGORIES = {
    "intake",
    "review",
    "governance",
    "trust",
    "transparency",
}

SUPPORTED_TEMPLATES = {
    "quarantine_external_bundles",
    "review_min_approvals",
    "require_policy_signature",
    "policy_signature_threshold_m",
    "trust_anchor_allowlist",
    "enable_transparency_checkpoints",
    "require_manifest_signature",
    "require_trusted_manifest_signer",
}


class NormRule(BaseModel):
    key: str
    value: Any


class Norm(BaseModel):
    norm_id: str
    statement: str
    category: str
    enforcement: str = Field(default="required", description="required|recommended|optional")
    rationale: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    compile_to: List[NormRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_norm(self) -> "Norm":
        if self.category not in SUPPORTED_CATEGORIES:
            raise ValueError(f"unsupported norm category: {self.category}")
        for rule in self.compile_to:
            if rule.key not in SUPPORTED_TEMPLATES:
                raise ValueError(f"unsupported compile_to rule: {rule.key}")
        return self


class NormSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    norm_set_id: str
    village_id: str
    title: str
    version: str
    description: str = ""
    authors: List[str] = Field(default_factory=list)
    created_at: datetime
    norms: List[Norm] = Field(default_factory=list)


class PolicyLineage(BaseModel):
    source_norm_set_id: str
    source_norm_ids: List[str]
    compiler_version: str
    compiler_ruleset: str
    output_policy_hash: str
    transformation_notes: List[str] = Field(default_factory=list)


class CompiledPolicyArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compiled_policy_id: str
    village_id: str
    title: str
    source_norm_set_id: str
    generated_at: datetime
    compiler: Dict[str, Any]
    policy: Dict[str, Any]
    policy_hash: str
    lineage: PolicyLineage
    source_norm_snapshot: List[Dict[str, Any]] = Field(default_factory=list)


class ContradictoryNormError(ValueError):
    pass


@dataclass
class CompilationResult:
    norm_set: NormSet
    artifact: CompiledPolicyArtifact


def _base_policy() -> Dict[str, Any]:
    return VillagePolicy().model_dump()


_TEMPLATE_NOTES = {
    "quarantine_external_bundles": "External claim bundles are quarantined pending review.",
    "review_min_approvals": "Quarantine review threshold compiled from village review norms.",
    "require_policy_signature": "Signed policy updates are required.",
    "policy_signature_threshold_m": "Policy signer quorum threshold compiled from governance norms.",
    "trust_anchor_allowlist": "Trust anchor allowlist compiled from trust norms.",
    "enable_transparency_checkpoints": "Transparency checkpoints enabled from publication norms.",
    "require_manifest_signature": "Signed policy manifests are required during pull operations.",
    "require_trusted_manifest_signer": "Trusted manifest signers are required during pull operations.",
}


def compile_norm_set(norm_set: NormSet, compiler_version: str = "0.15.0", compiler_ruleset: str = "norm-compiler-v1") -> CompilationResult:
    policy = _base_policy()
    source_norm_ids: List[str] = []
    notes: List[str] = []
    compiled_by_rule: Dict[str, Any] = {}

    for norm in norm_set.norms:
        source_norm_ids.append(norm.norm_id)
        for rule in norm.compile_to:
            if isinstance(rule, dict):
                rule = NormRule.model_validate(rule)
            key = rule.key
            value = rule.value
            if key in compiled_by_rule and compiled_by_rule[key] != value:
                raise ContradictoryNormError(
                    f"conflicting compiled values for {key}: {compiled_by_rule[key]!r} vs {value!r} (norm_id={norm.norm_id})"
                )
            compiled_by_rule[key] = value
            if key == "quarantine_external_bundles":
                policy["quarantine_external_bundles"] = bool(value)
            elif key == "review_min_approvals":
                iv = int(value)
                if iv < 1:
                    raise ContradictoryNormError("review_min_approvals must be >= 1")
                policy["quarantine_review_min_approvals"] = iv
            elif key == "require_policy_signature":
                policy["require_policy_signature"] = bool(value)
            elif key == "policy_signature_threshold_m":
                iv = int(value)
                if iv < 1:
                    raise ContradictoryNormError("policy_signature_threshold_m must be >= 1")
                policy["policy_signature_threshold_m"] = iv
            elif key == "trust_anchor_allowlist":
                if not isinstance(value, list):
                    raise ContradictoryNormError("trust_anchor_allowlist must be a list")
                policy["trusted_manifest_signer_allowlist"] = list(value)
            elif key == "enable_transparency_checkpoints":
                policy["transparency_checkpoints_enabled"] = bool(value)
            elif key == "require_manifest_signature":
                policy["require_manifest_signature"] = bool(value)
            elif key == "require_trusted_manifest_signer":
                policy["require_trusted_manifest_signer"] = bool(value)
            else:  # pragma: no cover
                raise ContradictoryNormError(f"unsupported compile key: {key}")
            notes.append(_TEMPLATE_NOTES.get(key, f"Compiled {key}"))

    if policy.get("policy_signature_threshold_m", 1) > 1 and not policy.get("require_policy_signature", False):
        raise ContradictoryNormError("policy signer threshold > 1 requires require_policy_signature=true")

    if policy.get("require_trusted_manifest_signer", False) and not policy.get("require_manifest_signature", False):
        raise ContradictoryNormError("trusted manifest signer enforcement requires manifest signatures to be required")

    policy_hash = sha256_hex(canonical_json(policy))
    lineage = PolicyLineage(
        source_norm_set_id=norm_set.norm_set_id,
        source_norm_ids=source_norm_ids,
        compiler_version=compiler_version,
        compiler_ruleset=compiler_ruleset,
        output_policy_hash=policy_hash,
        transformation_notes=notes,
    )
    artifact = CompiledPolicyArtifact(
        compiled_policy_id=f"{norm_set.village_id}-compiled-{norm_set.version}",
        village_id=norm_set.village_id,
        title=f"Compiled policy for {norm_set.title}",
        source_norm_set_id=norm_set.norm_set_id,
        generated_at=utc_now(),
        compiler={"version": compiler_version, "ruleset": compiler_ruleset},
        policy=policy,
        policy_hash=policy_hash,
        lineage=lineage,
        source_norm_snapshot=[n.model_dump() for n in norm_set.norms],
    )
    return CompilationResult(norm_set=norm_set, artifact=artifact)


def validate_norm_file(path: Path) -> NormSet:
    return NormSet.model_validate_json(path.read_text(encoding="utf-8"))


def init_norm_set(village_id: str, title: str | None = None, author: str = "operator") -> NormSet:
    return NormSet(
        norm_set_id=f"{village_id}-baseline-v1",
        village_id=village_id,
        title=title or f"{village_id} governance baseline",
        version="1.0.0",
        description="Starter norm set for PolicyMesh governance authoring.",
        authors=[author],
        created_at=utc_now(),
        norms=[
            Norm(
                norm_id="external-bundles-reviewed",
                statement="External claim bundles must be quarantined before acceptance.",
                category="intake",
                compile_to=[NormRule(key="quarantine_external_bundles", value=True)],
                tags=["intake", "quarantine"],
            ),
            Norm(
                norm_id="moderator-dual-review",
                statement="At least two reviewers must approve quarantined bundles.",
                category="review",
                compile_to=[NormRule(key="review_min_approvals", value=2)],
                tags=["review"],
            ),
            Norm(
                norm_id="signed-policy-updates",
                statement="Policy updates must carry approved signatures.",
                category="governance",
                compile_to=[
                    NormRule(key="require_policy_signature", value=True),
                    NormRule(key="policy_signature_threshold_m", value=2),
                ],
                tags=["governance", "signatures"],
            ),
        ],
    )


def diff_norm_sets(old: NormSet, new: NormSet) -> Dict[str, Any]:
    old_map = {n.norm_id: n for n in old.norms}
    new_map = {n.norm_id: n for n in new.norms}
    added = sorted([k for k in new_map.keys() if k not in old_map])
    removed = sorted([k for k in old_map.keys() if k not in new_map])
    changed = []
    for key in sorted(set(old_map.keys()).intersection(new_map.keys())):
        if old_map[key].model_dump() != new_map[key].model_dump():
            changed.append(key)
    return {
        "old_norm_set_id": old.norm_set_id,
        "new_norm_set_id": new.norm_set_id,
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def compiled_artifact_to_policy_update(artifact: CompiledPolicyArtifact, actor: Optional[str] = None, previous_policy_hash: Optional[str] = None) -> VillagePolicyUpdate:
    return build_update(
        village_id=artifact.village_id,
        policy=artifact.policy,
        actor=actor,
        lifecycle_state="approved",
        previous_policy_hash=previous_policy_hash,
        policy_version_id=artifact.compiled_policy_id,
        change_summary={"added": [], "removed": [], "changed": ["/policy"]},
    )


def apply_compiled_policy(root: Path, artifact: CompiledPolicyArtifact, actor: Optional[str] = None) -> None:
    apply_policy_update(
        root,
        artifact.village_id,
        artifact.policy,
        actor=actor,
        update_meta={
            "ts": utc_now().isoformat().replace("+00:00", "Z"),
            "policy_update": "norms.compile_apply",
            "compiled_policy_id": artifact.compiled_policy_id,
            "source_norm_set_id": artifact.source_norm_set_id,
            "policy_hash": artifact.policy_hash,
        },
    )


def write_json(path: Path, payload: BaseModel | Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, BaseModel):
        text = payload.model_dump_json(indent=2)
    else:
        text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    path.write_text(text + ("\n" if not text.endswith("\n") else ""), encoding="utf-8")
    return path
