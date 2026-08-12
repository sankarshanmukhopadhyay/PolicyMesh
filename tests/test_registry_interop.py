from links.registry_interop import ExternalRegistryArtifact, compare_registry


def test_registry_diff_requires_explicit_decision_on_change():
    artifact = ExternalRegistryArtifact(registry_id="r1", village_id="alpha", authority="example", policy={"visibility":"public"})
    report = compare_registry({"visibility":"village"}, artifact)
    assert report["decision_required"] is True
    assert report["policy_equal"] is False
