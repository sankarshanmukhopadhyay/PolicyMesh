# Production hardened profile (guidance)

## TLS & ingress
Links should be deployed **behind a TLS terminator** such as Nginx, Envoy, or an API gateway.
Run the Links process on loopback or a private network interface.

## Auth
- Use bearer tokens for management endpoints.
- Consider mTLS or gateway-level auth for stronger posture.

## Rate limiting
- The built-in limiter is a safety net, not a full perimeter control.
- Enforce real rate limiting at the gateway.
- Treat current defaults as suitable for controlled environments, not as an internet-facing abuse control system.

## Storage
- The filesystem backend is the simplest operator path and remains the default.
- A storage abstraction with an optional SQLite backend remains a next-increment priority.
- Move to a stronger backend if you need higher concurrency, cleaner transaction boundaries, or easier recovery semantics.

## Observability
- Export audit logs periodically (`/audit/export` or `links audit export`).
- Ship logs to your SIEM or equivalent operational log sink.
- Add periodic drift checks and policy snapshot handling as part of routine operations.
