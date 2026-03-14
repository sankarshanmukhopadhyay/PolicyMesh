# Manifest Trust Bootstrap and Rotation

Links can now evaluate remote policy feed manifests against local village policy.

## Policy fields

Add these fields to village policy when a node should fail closed during pull operations:

- `trusted_manifest_signer_allowlist`: trusted manifest signer key hashes
- `require_manifest_signature`: require remote manifests to be signed
- `require_trusted_manifest_signer`: require the signer to be in the allowlist

## Bootstrap pattern

1. generate or designate a node signing key for the remote publisher
2. compute the key hash from the Ed25519 public key
3. distribute that hash through an out-of-band governance channel
4. add the hash to `trusted_manifest_signer_allowlist`
5. set `require_manifest_signature=true`
6. set `require_trusted_manifest_signer=true` once peers have the pinned hash

This gives operators a staged rollout path instead of a theatrical cliff dive.

## Rotation pattern

1. publish the new signer hash in governance materials before cutover
2. temporarily include both old and new hashes in the allowlist
3. confirm that peers can validate manifests from the new signer
4. remove the old signer hash after the cutover window closes

## Operational notes

- development nodes can continue to accept unsigned manifests by leaving both requirement flags unset
- production or cross-organization federation should generally require both signature presence and trusted signer pinning
- manifest trust does not replace policy update signature checks; it adds trust to the feed envelope itself
