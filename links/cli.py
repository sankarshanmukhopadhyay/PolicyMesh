from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json
import base64
import typer
import requests

from nacl.signing import SigningKey

from links.server import create_app
from links.policy_updates import VillagePolicyUpdate, verify_update_any, add_signature, sign_update_legacy, build_update, compute_policy_hash
from links.policy_diff import diff_policies
from links.policy_feed import PolicyFeedManifest, fill_history_gaps, verify_manifest_against_policy
from links.reconcile import reconcile, write_reconciliation_report
from links.trust_anchors import TrustAnchorEntry, add_anchor_signature, verify_anchor_entry_any
from links.policy_feed import signer_allowed
from links.validate import validate_village_id
from links.transparency import write_transparency_checkpoint

try:
    from links.villages import apply_policy_update, load_village  # type: ignore
except Exception:  # pragma: no cover
    apply_policy_update = None
    load_village = None

app = typer.Typer(help="Links: verifiable claim exchange with group policy controls.")
policy = typer.Typer(help="Policy feed operations")
anchors = typer.Typer(help="Trust anchor registry operations")
app.add_typer(policy, name="policy")
app.add_typer(anchors, name="anchors")


@app.command("serve")
def serve(host: str = "127.0.0.1", port: int = 8080):
    import ipaddress
    import uvicorn

    # Operational hardening: if you bind to a non-loopback interface, assume you're behind TLS termination.
    try:
        ip = ipaddress.ip_address(host)
        is_loopback = ip.is_loopback
    except Exception:
        is_loopback = host in ("localhost", "127.0.0.1", "::1")

    if not is_loopback:
        typer.echo("WARNING: Binding to a non-loopback interface. Run Links behind a TLS terminator (e.g., Nginx/Envoy) and use proper auth/rate limiting.", err=True)

    uvicorn.run(create_app(), host=host, port=port)


@policy.command("sign-add")
def policy_sign_add(inp: Path, key: Path, out: Path):
    """
    Append a signer signature to a policy update artifact (multisig quorum).
    """
    u = VillagePolicyUpdate.model_validate_json(inp.read_text(encoding="utf-8"))
    seed = base64.b64decode(key.read_text(encoding="utf-8").strip())
    sk = SigningKey(seed[:32])
    s = add_signature(u, sk)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(s.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote {out}")


@policy.command("sign-legacy")
def policy_sign_legacy(inp: Path, key: Path, out: Path):
    """
    Produce a legacy single-signature policy update (public_key + signature).
    """
    u = VillagePolicyUpdate.model_validate_json(inp.read_text(encoding="utf-8"))
    seed = base64.b64decode(key.read_text(encoding="utf-8").strip())
    sk = SigningKey(seed[:32])
    s = sign_update_legacy(u, sk)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(s.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote {out}")


@policy.command("verify")
def policy_verify(inp: Path):
    u = VillagePolicyUpdate.model_validate_json(inp.read_text(encoding="utf-8"))
    ok = verify_update_any(u)
    typer.echo("OK" if ok else "FAIL")
    raise typer.Exit(code=0 if ok else 1)


@policy.command("pull")
def policy_pull(url: str, village_id: str, apply: bool = True, since: str = None, token: str = None, page_limit: int = 200):
    """
    Pull policy updates from a remote node using:
      1) Signed manifest (if available)
      2) Paginated updates (large-history optimization)

    Reconcile rule (default): select latest update by (created_at, policy_hash).
    Also prints fork detection signals when previous_policy_hash links diverge.
    """
    validate_village_id(village_id)
    base = url.rstrip("/")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # 1) Fetch manifest (optional but preferred)
    manifest = None
    try:
        mr = requests.get(f"{base}/villages/{village_id}/policy/manifest", headers=headers, timeout=30)
        if mr.status_code == 200:
            manifest = mr.json()
    except Exception:
        manifest = None

    # 2) Fetch updates (paginated if supported)
    updates = []
    try:
        cursor = None
        while True:
            pr = requests.get(
                f"{base}/villages/{village_id}/policy/updates_page",
                params={"since": since, "cursor": cursor, "limit": page_limit},
                headers=headers,
                timeout=30,
            )
            if pr.status_code != 200:
                raise RuntimeError("updates_page not supported")
            payload = pr.json()
            updates.extend([VillagePolicyUpdate.model_validate(u) for u in payload.get("items", [])])
            cursor = payload.get("next_cursor")
            if not cursor:
                break
    except Exception:
        # fallback: legacy endpoint
        endpoint = f"{base}/villages/{village_id}/policy/updates"
        params = {}
        if since:
            params["since"] = since
        r = requests.get(endpoint, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        updates = [VillagePolicyUpdate.model_validate(u) for u in r.json()]

    if not updates:
        typer.echo("No updates.")
        raise typer.Exit(code=0)

    # Verify signature material (if any) for each update.
    for u in updates:
        has_any = bool(u.signatures) or bool(u.public_key) or bool(u.signature)
        if has_any and not verify_update_any(u):
            typer.echo(f"Invalid signature material for update policy_hash={u.policy_hash}")
            raise typer.Exit(code=1)

    local_updates = []
    try:
        from links.policy_feed import list_policy_updates
        local_updates = list_policy_updates(Path("data"), village_id)
    except Exception:
        local_updates = []

    current_policy = {}
    if load_village:
        try:
            v = load_village(Path("data"), village_id)
            current_policy = v.policy.model_dump()
        except Exception:
            current_policy = {}

    manifest_ok = None
    manifest_msg = None
    if manifest:
        try:
            m = PolicyFeedManifest.model_validate(manifest)
            manifest_ok, manifest_msg = verify_manifest_against_policy(current_policy, m)
        except Exception as exc:
            manifest_ok, manifest_msg = False, f"manifest validation failed: {exc}"
        if manifest_ok is False:
            typer.echo(f"Manifest validation failed: {manifest_msg}")
            raise typer.Exit(code=1)

    local_hashes = {u.policy_hash for u in local_updates}
    def _fetch_update_by_hash(policy_hash: str):
        try:
            resp = requests.get(f"{base}/villages/{village_id}/policy/by_hash/{policy_hash}", headers=headers, timeout=30)
            if resp.status_code != 200:
                return None
            return VillagePolicyUpdate.model_validate(resp.json())
        except Exception:
            return None

    updates, fetched_parent_hashes, unresolved_parent_hashes = fill_history_gaps(
        updates,
        known_policy_hashes=local_hashes,
        fetch_update_by_hash=_fetch_update_by_hash,
    )

    report = reconcile(local_updates, updates, village_id=village_id)
    chosen_hash = report.selected_head
    chosen = next((u for u in updates if u.policy_hash == chosen_hash), None)
    if chosen is None:
        updates.sort(key=lambda u: (u.created_at, u.policy_hash), reverse=True)
        chosen = updates[0]

    # Drift detection (best-effort)
    local_hash = None
    if load_village:
        try:
            v = load_village(Path("data"), village_id)
            local_hash = __import__("links.policy_updates", fromlist=["compute_policy_hash"]).compute_policy_hash(v.policy.model_dump())
        except Exception:
            local_hash = None

    typer.echo(f"Selected policy_hash={chosen.policy_hash} source={report.selected_source} status={report.status}")
    typer.echo(f"Selection reason: {report.selection_reason}")
    if local_hash and local_hash != chosen.policy_hash:
        typer.echo(f"Drift detected: local={local_hash} remote_selected={chosen.policy_hash}")
    if manifest_msg:
        typer.echo(f"Manifest: {manifest_msg}")

    rec_out_dir = Path("artifacts/reconciliation") / village_id
    rec_out_dir.mkdir(parents=True, exist_ok=True)
    rec_out = rec_out_dir / f"pull.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_reconciliation_report(report, rec_out)
    typer.echo(f"Wrote {rec_out}")

    if fetched_parent_hashes:
        typer.echo(f"Recovered parent chain updates: {len(fetched_parent_hashes)}")
    if unresolved_parent_hashes:
        typer.echo(f"Warning: unresolved parent hashes remain: {', '.join(unresolved_parent_hashes[:10])}")

    if apply and apply_policy_update:
        ok, msg = signer_allowed(current_policy, chosen)
        if not ok:
            typer.echo(f"Refusing to apply update: {msg}")
            raise typer.Exit(code=1)

        apply_policy_update(Path("data"), village_id, chosen.policy, actor=chosen.actor or "pull", update_meta={"policy_hash": chosen.policy_hash, "policy_update": "pull"})
        typer.echo("Applied.")
    else:
        typer.echo("Not applied (apply=false or local apply not available).")

    out_dir = Path("artifacts/policy_feed") / village_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"latest.{chosen.policy_hash}.json"
    out.write_text(chosen.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote {out}")
    if manifest is not None:
        man_out = out_dir / f"manifest.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        man_out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        typer.echo(f"Wrote {man_out}")



def _load_updates_from_path(path: Path) -> list[VillagePolicyUpdate]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [VillagePolicyUpdate.model_validate(x) for x in raw]
    if isinstance(raw, dict) and isinstance(raw.get("items"), list):
        return [VillagePolicyUpdate.model_validate(x) for x in raw.get("items", [])]
    if isinstance(raw, dict):
        return [VillagePolicyUpdate.model_validate(raw)]
    raise typer.BadParameter(f"Unsupported reconciliation input: {path}")


@policy.command("reconcile")
def policy_reconcile(local: Path, remote: Path, village_id: str, out: Path = typer.Option(None, help="Optional JSON report output path")):
    """
    Reconcile local and remote policy update artifacts and write a durable report.
    """
    validate_village_id(village_id)
    local_updates = _load_updates_from_path(local)
    remote_updates = _load_updates_from_path(remote)
    report = reconcile(local_updates, remote_updates, village_id=village_id)

    if out is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = Path("artifacts/reconciliation") / village_id / f"reconciliation.{stamp}.json"
    write_reconciliation_report(report, out)
    typer.echo(json.dumps(report.to_dict(), indent=2))
    typer.echo(f"Wrote {out}")

@policy.command("drift")
def policy_drift(url: str, village_id: str, token: str = None, out: Path = typer.Option(None, help="Optional JSON output path")):
    """
    Compare local policy hash to remote latest policy hash and optionally write a durable artifact.
    """
    validate_village_id(village_id)
    base = url.rstrip("/")
    endpoint = f"{base}/villages/{village_id}/policy/latest"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(endpoint, headers=headers, timeout=30)
    r.raise_for_status()
    remote = VillagePolicyUpdate.model_validate(r.json())
    remote_hash = remote.policy_hash

    local_hash = None
    if load_village:
        try:
            v = load_village(Path("data"), village_id)
            local_hash = compute_policy_hash(v.policy.model_dump())
        except Exception:
            local_hash = None

    payload = {
        "village_id": village_id,
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "local_policy_hash": local_hash,
        "remote_policy_hash": remote_hash,
        "drift": (local_hash != remote_hash),
        "status": "drift" if local_hash != remote_hash else "aligned",
        "source_url": base,
    }

    if out is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = Path("artifacts/drift") / village_id / f"drift.{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    typer.echo(json.dumps(payload, indent=2))
    typer.echo(f"Wrote {out}")


# -----------------------------
# Audit / Observability
# -----------------------------
audit = typer.Typer(help="Audit trails, exports, and digests.")
app.add_typer(audit, name="audit")

@audit.command("export")
def audit_export_cmd(village_id: str, fmt: str = typer.Option("json", help="json|csv"), out: Path = typer.Option(Path("audit_export"), help="Output dir"), sign: bool = typer.Option(True, help="Sign digest with node key (env LINKS_NODE_SIGNING_KEY_B64)")):
    """Export audit log for a village to JSON or CSV and optionally sign the digest."""
    from .audit_export import export_audit_json, export_audit_csv, sign_digest_hex
    from .keys import load_signing_key_from_env
    from .file_lock import locked_open
    from .validate import validate_village_id
    import json as _json

    validate_village_id(village_id)
    store_root = Path("data/store")
    audit_path = store_root / "audit" / "audit.log.jsonl"
    if not audit_path.exists():
        raise typer.Exit(code=2)

    out.mkdir(parents=True, exist_ok=True)
    filtered = out / f"{village_id}.audit.filtered.jsonl"
    with locked_open(audit_path, "r") as f_in, locked_open(filtered, "w") as f_out:
        for line in f_in:
            try:
                ev = _json.loads(line)
            except Exception:
                continue
            if ev.get("village_id") == village_id:
                f_out.write(_json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")

    target = out / f"{village_id}.audit.{fmt}"
    if fmt == "json":
        digest, count = export_audit_json(filtered, target)
    elif fmt == "csv":
        digest, count = export_audit_csv(filtered, target)
    else:
        raise typer.BadParameter("fmt must be json or csv")

    sig = None
    if sign:
        try:
            sk = load_signing_key_from_env()
            sig = sign_digest_hex(digest, sk)
            (target.with_suffix(target.suffix + ".sha256")).write_text(digest + "\n", encoding="utf-8")
            (target.with_suffix(target.suffix + ".sighex")).write_text(sig + "\n", encoding="utf-8")
        except Exception:
            pass

    typer.echo(_json.dumps({"village_id": village_id, "format": fmt, "count": count, "sha256": digest, "signed": bool(sig), "path": str(target)}, indent=2))



# -----------------------------
# Registry I/O (Ecosystem)
# -----------------------------
registry = typer.Typer(help="Import/export village registry artifacts.")
app.add_typer(registry, name="registry")

@registry.command("export")
def registry_export(village_id: str, out: Path = typer.Option(Path("registry_export.json"), help="Output JSON file")):
    """Export a minimal trust-registry artifact (members, revocations, anchors, policy head)."""
    from .validate import validate_village_id
    from .villages import load_village, _members_path, _revocations_path
    validate_village_id(village_id)
    root = Path("data")
    v = load_village(root, village_id)
    members = _members_path(root, village_id).read_text(encoding="utf-8").splitlines()
    revocations = _revocations_path(root, village_id).read_text(encoding="utf-8").splitlines()
    anchors_path = Path("data/store") / "anchors" / village_id / "anchors.jsonl"
    anchors = []
    if anchors_path.exists():
        anchors = [json.loads(l) for l in anchors_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    payload = {
        "format": "links.external_registry.v1",
        "village_id": village_id,
        "policy": v.policy.model_dump(),
        "members": [m for m in members if m.strip()],
        "revocations": [r for r in revocations if r.strip()],
        "trust_anchors": anchors,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    typer.echo(str(out))

@registry.command("import")
def registry_import(path: Path):
    """Import a minimal trust-registry artifact into local data/ (best-effort)."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    village_id = payload.get("village_id")
    from .validate import validate_village_id
    validate_village_id(village_id)
    root = Path("data")
    # write village policy
    from .villages import save_village, Village
    v = Village(village_id=village_id, policy=payload.get("policy", {}), capabilities={})
    save_village(root, v)
    # members/revocations
    (root / "villages" / village_id).mkdir(parents=True, exist_ok=True)
    (root / "villages" / village_id / "members.jsonl").write_text("\n".join(payload.get("members", [])) + "\n", encoding="utf-8")
    (root / "villages" / village_id / "revocations.jsonl").write_text("\n".join(payload.get("revocations", [])) + "\n", encoding="utf-8")
    typer.echo(f"Imported village {village_id}")


# -----------------------------
# Drift monitoring
# -----------------------------
drift = typer.Typer(help="Drift checks and alert hooks.")
app.add_typer(drift, name="drift")

@drift.command("checkpoint")
def drift_checkpoint(village_id: str, out: Path = typer.Option(None, help="Optional output path for transparency checkpoint JSON")):
    """Write a transparency checkpoint artifact for a village."""
    validate_village_id(village_id)
    if out is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = Path("artifacts/transparency") / village_id / f"checkpoint.{stamp}.json"
    write_transparency_checkpoint(Path("data/store"), village_id, out)
    typer.echo(f"Wrote {out}")


@drift.command("check")
def drift_check(village_id: str, remote_base: str = typer.Option(..., help="Remote node base URL"), webhook: str = typer.Option("", help="Optional webhook URL for alerts")):
    """Compare local policy head vs remote manifest head and emit a severity classification."""
    from .validate import validate_village_id
    from .villages import load_village
    from .policy_updates import compute_policy_hash
    validate_village_id(village_id)

    remote = requests.get(f"{remote_base}/villages/{village_id}/policy/manifest", timeout=10)
    remote.raise_for_status()
    man = remote.json()
    remote_head = man.get("head")
    local_head = None
    try:
        v = load_village(Path("data"), village_id)
        local_head = compute_policy_hash(v.policy.model_dump())
    except Exception:
        local_head = None

    drifted = (local_head != remote_head)
    forks = man.get("forks", []) if isinstance(man, dict) else []
    severity = "none"
    if drifted:
        severity = "high"
    if forks:
        severity = "critical"

    report = {"village_id": village_id, "local_head": local_head, "remote_head": remote_head, "drift": drifted, "forks": forks, "severity": severity}
    typer.echo(json.dumps(report, indent=2))

    if webhook:
        try:
            requests.post(webhook, json=report, timeout=10)
        except Exception:
            pass
