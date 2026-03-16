from pathlib import Path

import pytest

from links.norms import (
    validate_norm_file,
    compile_norm_set,
    ContradictoryNormError,
    diff_norm_sets,
    init_norm_set,
)


def test_validate_and_compile_example():
    ns = validate_norm_file(Path("examples/norms/ops-moderation.json"))
    result = compile_norm_set(ns)
    assert result.artifact.source_norm_set_id == "ops-moderation-v1"
    assert result.artifact.policy["require_policy_signature"] is True
    assert result.artifact.policy["policy_signature_threshold_m"] == 2
    assert result.artifact.lineage.source_norm_ids == [
        "external-bundles-reviewed",
        "moderator-dual-review",
        "signed-policy-updates",
    ]


def test_compilation_is_deterministic_for_policy_content():
    ns = validate_norm_file(Path("examples/norms/ops-moderation.json"))
    r1 = compile_norm_set(ns)
    r2 = compile_norm_set(ns)
    assert r1.artifact.policy == r2.artifact.policy
    assert r1.artifact.policy_hash == r2.artifact.policy_hash


def test_contradictory_norms_fail():
    ns = init_norm_set("ops")
    ns.norms.append(
        ns.norms[0].model_copy(update={
            "norm_id": "external-bundles-autoaccept",
            "compile_to": [{"key": "quarantine_external_bundles", "value": False}],
        })
    )
    with pytest.raises(ContradictoryNormError):
        compile_norm_set(ns)


def test_diff_norm_sets():
    old = init_norm_set("ops")
    new = old.model_copy(deep=True)
    new.norms = new.norms[1:]
    new.norms.append(new.norms[0].model_copy(update={"norm_id": "new-rule"}))
    report = diff_norm_sets(old, new)
    assert "external-bundles-reviewed" in report["removed"]
    assert "new-rule" in report["added"]
