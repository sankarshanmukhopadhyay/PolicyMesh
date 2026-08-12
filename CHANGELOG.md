# Changelog

## Unreleased

### Fixed
- declare the `httpx2` test dependency required by current Starlette `TestClient`, preventing CI collection failures;
- move the GitHub Pages site to Just the Docs and enable supported Mermaid rendering.

### Documentation
- add an explicit PolicyMesh ↔ DTG interoperability and authority-boundary model;
- connect Trust Tasks, Trust Ceremonies, credentials, ZKP, RAHP, VDS, and implementation work to PolicyMesh without asserting DTG normative status;
- expand architecture, authority-boundary, README, and documentation navigation material.

## v0.18.0 — Governed lifecycle, assurance evidence, and repository readiness

### Added
- explicit proposal → approved → active → rolled-back lifecycle transition validation;
- deterministic rollback to retained historical policy state;
- trust-anchor register, rotate, revoke, inspect, and history operator workflows;
- portable policy evidence bundles with digest verification;
- governed cryptographic algorithm lifecycle;
- versioned external-registry interchange with validate/diff and explicit apply/defer/reject decisions;
- optional authority-context evidence on policy updates;
- deployment profiles, machine-readable control/evidence mappings, repository status contract, governance and security policies;
- repository validation workflow and GitHub Pages validation/deployment workflow.

### Changed
- ROADMAP reconciled against implementation evidence: stale Partial labels removed and completed capabilities recorded as shipped within declared scope;
- README and documentation architecture reorganized around adoption, architecture, operations, interoperability, assurance, and governance;
- package version advanced to 0.18.0.

### Security
- registry imports no longer represent a silent overwrite workflow;
- lifecycle state changes invalidate prior signatures and require re-signing;
- cryptographic acceptance now has explicit supported/deprecated/prohibited states.
