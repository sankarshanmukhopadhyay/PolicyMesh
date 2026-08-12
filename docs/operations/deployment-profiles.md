# Deployment profiles

Versioned profiles live in `config/profiles/`:

- `development.yaml` for loopback/local evaluation;
- `federation-pilot.yaml` for authenticated small-node interoperability testing;
- `production-hardened.yaml` for explicit hardening expectations.

The production-hardened profile is guidance, not certification. Operators remain responsible for TLS termination, secret custody, authentication, backups, monitoring, infrastructure hardening and incident response.
