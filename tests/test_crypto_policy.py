from links.crypto_policy import CryptographicPolicy, AlgorithmRule


def test_crypto_policy_defaults_and_unknowns():
    policy = CryptographicPolicy()
    assert policy.permits("ed25519")[0]
    assert policy.permits("ecdsa_p256")[0]
    assert not policy.permits("rsa1024")[0]


def test_deprecated_is_permitted_with_warning_state():
    policy = CryptographicPolicy(algorithms=[AlgorithmRule(name="ed25519", state="deprecated")])
    ok, state = policy.permits("ed25519")
    assert ok
    assert state == "deprecated"
