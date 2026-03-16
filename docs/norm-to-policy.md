# Norm to Policy Compilation

The v0.15.0 compiler translates structured norms into executable village policy fields.

## Mapping model

| Norm template | Compiled field |
|---|---|
| `quarantine_external_bundles` | `quarantine_external_bundles` |
| `review_min_approvals` | `quarantine_review_min_approvals` |
| `require_policy_signature` | `require_policy_signature` |
| `policy_signature_threshold_m` | `policy_signature_threshold_m` |
| `require_manifest_signature` | `require_manifest_signature` |
| `require_trusted_manifest_signer` | `require_trusted_manifest_signer` |
| `enable_transparency_checkpoints` | `transparency_checkpoints_enabled` |

## Determinism

The same `NormSet` produces the same compiled policy content and therefore the same `policy_hash`.

## Contradiction handling

Compilation fails when two norms compile to conflicting values for the same template or when a dependent control is impossible. Examples:

- signer threshold greater than one while policy signatures are disabled
- trusted manifest signer enforcement without manifest signatures
- invalid review threshold values

## Provenance

Compiled artifacts include:

- source norm set ID
- source norm IDs
- compiler version and ruleset
- output policy hash
- transformation notes

This makes the resulting policy inspectable rather than magical.
