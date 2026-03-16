from pathlib import Path

from links.norms import validate_norm_file, compile_norm_set, apply_compiled_policy
from links.villages import Village, VillageGovernance, VillagePolicy, save_village, load_village
from links.utils import utc_now


def test_apply_compiled_policy(tmp_path: Path):
    root = tmp_path / "data"
    village = Village(
        village_id="ops",
        name="Ops",
        created_at=utc_now(),
        governance=VillageGovernance(admins=["alice"]),
        policy=VillagePolicy(),
    )
    save_village(root, village)
    ns = validate_norm_file(Path("examples/norms/ops-moderation.json"))
    result = compile_norm_set(ns)
    apply_compiled_policy(root, result.artifact, actor="tester")
    loaded = load_village(root, "ops")
    assert loaded.policy.require_policy_signature is True
    assert loaded.policy.policy_signature_threshold_m == 2
    assert getattr(loaded.policy, "quarantine_external_bundles") is True
