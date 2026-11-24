# Authoring scenario indexes

See the [case-study method](../../docs/examples/governance-case-study-method.md). Each domain maintains a `scenarios.json` index. Each row names an existing request/expected pair, expected local decision, human-readable rationale, and optional DTFC correlations. DTFC links pin the reviewed corpus revision and case version. Relationships are illustrative only.

Add new requests and expected files together; reuse existing policy and context fixtures unless the new proposition requires a change. Run the domain runner and the index tests. Do not infer external execution, current authority or canonical failure-case satisfaction from local evaluation. Keep hypothetical lifecycle states in the domain guide, not the executable index.
