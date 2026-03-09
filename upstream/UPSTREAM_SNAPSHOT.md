# Upstream snapshot

This directory contains an unmodified snapshot of the upstream repository content as provided via `Links-upstream.zip`.

- Snapshot date: 2026-02-23
- Source artifact: Links-upstream.zip (provided out-of-band)
- Purpose: preserve the upstream baseline and make divergence easy to inspect

## Delta note

The current fork has diverged materially from the upstream snapshot.

Upstream primarily reflects an earlier prototype centered on village concepts, lightweight utilities, and an initial Wikipedia-oriented harvesting approach.
The fork now contains a substantially broader implementation surface, including:

- a maintained `links/` package with CLI and server components
- claim bundle handling and verification flows
- village membership and governance controls
- policy updates, pull workflows, drift checks, quarantine, and trust anchors
- schemas, examples, tests, deployment docs, and release notes
- a more developed Wikipedia ingestion pipeline under `pipelines/wikipedia/`

## Intake posture

No wholesale vendoring from upstream is applied in this increment.
Selective upstream intake remains possible where a change is both substantively useful and easy to preserve with clear provenance.

Fork-specific enhancements live in the repository root, while this directory remains a historical reference point for comparison.
