# SQLite Backend

Links continues to default to a filesystem-first storage model. For operators who want a more durable single-node or small-team deployment profile, `v0.13.0` adds an optional SQLite backend.

## Why use it

Use the SQLite backend when you want:

- stronger local durability than JSONL-only indexing
- transaction boundaries for policy state writes
- easier backup and restore for a single node pilot
- a cleaner path from developer workstation to modest production trial

This is not a clustered database mode. It is the practical middle ground between a toy folder tree and a full external database stack.

## Enable it

```bash
export LINKS_STORAGE_BACKEND=sqlite
export LINKS_SQLITE_PATH=data/store/links.sqlite3
```

Then run Links as usual.

## What is stored in SQLite

When the SQLite backend is enabled, Links writes structured records for:

- claim index rows
- bundle registry metadata
- audit events
- transparency entries
- current policy state and policy history

Filesystem artifacts are still written as the default operational surface. SQLite complements them with a more durable query and recovery layer.

## Atomicity model

Policy application now records current policy state and policy history in a transactional SQLite path. Filesystem artifacts remain the operator-facing source tree, while SQLite provides a more durable state ledger for recovery and inspection.

In plain English: fewer weird half-written goblins during local crashes.

## Backup and restore

A conservative backup pattern is:

1. stop write-heavy operations
2. copy `data/store/links.sqlite3`
3. copy `data/villages/` and `data/store/transparency/`
4. restart the service

For small deployments, taking both the SQLite file and the filesystem artifacts gives the cleanest rollback posture.
