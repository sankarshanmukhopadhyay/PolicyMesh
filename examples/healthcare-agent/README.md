# Healthcare Appointment & Consent Agent

This example separates **scheduling authority** from **information-disclosure authority**. A personal health agent can book an authorised specialty with a verified provider, but data sharing is evaluated against a separate purpose-limited disclosure policy.

```bash
python examples/healthcare-agent/run.py all
```

Scenarios demonstrate permitted dermatology booking, provider-verification deferral, out-of-scope specialty denial, permitted dermatology-history disclosure, prohibited full-record disclosure, explicit-consent deferral for raw genetic data, re-evaluation after consent, and mandate revocation.

The point is architectural: **being allowed to arrange care does not imply being allowed to disclose everything the agent can access**. New consent is modeled as new evidence that can change a previous `DEFER` into `PERMIT`.
