from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class ExternalRegistryArtifact(BaseModel):
    format: str = "links.external_registry.v2"
    registry_id: str
    village_id: str
    authority: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    policy: dict
    members: List[str] = Field(default_factory=list)
    revocations: List[str] = Field(default_factory=list)
    trust_anchors: List[dict] = Field(default_factory=list)
    provenance: dict = Field(default_factory=dict)


def compare_registry(local_policy: dict, incoming: ExternalRegistryArtifact) -> dict:
    return {
        "village_id": incoming.village_id,
        "registry_id": incoming.registry_id,
        "policy_equal": local_policy == incoming.policy,
        "incoming_member_count": len(incoming.members),
        "incoming_revocation_count": len(incoming.revocations),
        "incoming_anchor_count": len(incoming.trust_anchors),
        "decision_required": local_policy != incoming.policy,
    }
