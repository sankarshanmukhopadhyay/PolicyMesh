from __future__ import annotations

from typing import Dict, List, Literal, Tuple
from pydantic import BaseModel, Field

AlgorithmState = Literal["supported", "deprecated", "prohibited"]


class AlgorithmRule(BaseModel):
    name: str
    state: AlgorithmState
    reason: str = ""


class CryptographicPolicy(BaseModel):
    format: str = "links.crypto.policy.v1"
    default: str = "ed25519"
    algorithms: List[AlgorithmRule] = Field(default_factory=lambda: [
        AlgorithmRule(name="ed25519", state="supported", reason="default signing algorithm"),
        AlgorithmRule(name="ecdsa_p256", state="supported", reason="interoperability option"),
    ])

    def state_for(self, algorithm: str) -> AlgorithmState:
        name = algorithm.lower()
        for rule in self.algorithms:
            if rule.name.lower() == name:
                return rule.state
        return "prohibited"

    def permits(self, algorithm: str) -> Tuple[bool, str]:
        state = self.state_for(algorithm)
        if state == "supported":
            return True, "supported"
        if state == "deprecated":
            return True, "deprecated"
        return False, "prohibited or unknown algorithm"
