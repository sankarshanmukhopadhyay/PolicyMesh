# PolicyMesh

PolicyMesh is a verifiable claim exchange with group policy controls, policy governance artifacts, and operator-facing reconciliation workflows.

## What is here

- [Repository on GitHub](https://github.com/sankarshanmukhopadhyay/PolicyMesh)
- [Published roadmap](ROADMAP.md)
- [Policy governance](policy-governance.md)
- [Risk crosswalk](risk-crosswalk.md)
- [Ethics](ethics.md)
- [Risks](risks.md)
- [GitHub Pages deployment](deploy/pages.md)
- [Release notes v0.17.0](release-notes/v0.17.0.md)

## Earlier operator surfaces

- Durable reconciliation reports under `artifacts/reconciliation/`
- Cron-friendly drift reports under `artifacts/drift/`
- GitHub Actions workflows for tests and Pages deployment
- Backwards-compatible policy update construction for governance metadata


## v0.15.0 governance authoring

- Norm engine documentation: [norm-engine.md](./norm-engine.md)
- Norm-to-policy mapping: [norm-to-policy.md](./norm-to-policy.md)
- Release notes: [release-notes/v0.15.0.md](./release-notes/v0.15.0.md)


## v0.17.0 federation and operator surfaces

- Live checkpoint endpoint: `GET /villages/{village_id}/transparency/checkpoint`
- Live capability endpoint: `GET /nodes/capability`
- Quorum inspection CLI: `links policy quorum-inspect <village_id>`
- Release notes: [release-notes/v0.17.0.md](./release-notes/v0.17.0.md)
