from __future__ import annotations

from pathlib import Path
from typing import List
from datetime import datetime, timezone
import json
import base64
import typer
import requests

from nacl.signing import SigningKey

from links.server import create_app
from links.policy_updates import VillagePolicyUpdate, verify_update_any, add_signature, sign_update_legacy, build_update, compute_policy_hash
from links.decision_receipts import (
    ReceiptEvidence,
    PolicyDecisionReceipt,
    build_policy_decision_receipt,
    build_quorum_summary,
    evaluate_policy_update,
    sign_receipt,
    verify_receipt,
    write_receipt,
)
from links.policy_diff import diff_policies
from links.policy_feed import PolicyFeedManifest, fill_history_gaps, verify_manifest_against_policy
from links.reconcile import reconcile, write_reconciliation_report
from links.trust_anchors import TrustAnchorEntry, add_anchor_signature, verify_anchor_entry_any
from links.policy_feed import signer_allowed
from links.validate import validate_village_id
from links.transparency import write_transparency_checkpoint

from links.norms import (
    init_norm_set,
    validate_norm_file,
    compile_norm_set,
    write_json as write_norm_json,
    diff_norm_sets,
    apply_compiled_policy,
    CompiledPolicyArtifact,
    ContradictoryNormError,
)

try:
    from links.villages import apply_policy_update, load_village  # type: ignore
except Exception:  # pragma: no cover
    apply_policy_update = None
    load_village = None

app = typer.Typer(help="PolicyMesh: verifiable claim exchange with group policy controls.")
policy = typer.Typer(help="Policy feed operations")
anchors = typer.Typer(help="Trust anchor registry operations")
norms = typer.Typer(help="Norm authoring and compilation operations")
app.add_typer(policy, name="policy")
app.add_typer(anchors, name="anchors")
app.add_typer(norms, name="norms")


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
        typer.echo("WARNING: Binding to a non-loopback interface. Run PolicyMesh behind a TLS terminator (e.g., Nginx/Envoy) and use proper auth/rate limiting.", err=True)

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


@policy.command("verify-receipt")
def policy_verify_receipt(inp: Path):
    receipt = PolicyDecisionReceipt.model_validate_json(inp.read_text(encoding="utf-8"))
    ok = verify_receipt(receipt)
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

    signer_ok, signer_msg = signer_allowed(current_policy, chosen)
    decision, reason_codes, decision_notes = evaluate_policy_update(
        current_policy,
        chosen,
        manifest_ok=manifest_ok,
        signer_ok=signer_ok,
        signer_message=signer_msg,
    )

    if apply and apply_policy_update and decision == "apply":
        apply_policy_update(Path("data"), village_id, chosen.policy, actor=chosen.actor or "pull", update_meta={"policy_hash": chosen.policy_hash, "policy_update": "pull"})
        typer.echo("Applied.")
    elif decision == "defer":
        typer.echo(f"Deferred apply: {', '.join(reason_codes)}")
    elif decision == "reject":
        typer.echo(f"Refusing to apply update: {', '.join(reason_codes)}")
    else:
        typer.echo("Not applied (apply=false or local apply not available).")

    receipt = build_policy_decision_receipt(
        village_id=village_id,
        update=chosen,
        decision=decision if apply else "defer",
        reason_codes=reason_codes if apply else ["apply_skipped"],
        notes=decision_notes if apply else ["Policy update was fetched and reconciled but not applied because apply=false or local apply is unavailable."],
        actor=chosen.actor or "pull",
        action="policy_pull",
        local_policy_hash=local_hash,
        evidence=ReceiptEvidence(
            selected_source=report.selected_source,
            selected_head=report.selected_head,
            selection_reason=report.selection_reason,
            manifest_ok=manifest_ok,
            manifest_message=manifest_msg,
            reconciliation_status=report.status,
            reconciliation_report_path=str(rec_out),
            fetched_parent_hashes=fetched_parent_hashes,
            unresolved_parent_hashes=unresolved_parent_hashes,
            quorum_summary=build_quorum_summary(chosen),
        ),
    )

    signing_key_b64 = None
    try:
        import os
        signing_key_b64 = os.environ.get("LINKS_NODE_SIGNING_KEY_B64")
    except Exception:
        signing_key_b64 = None
    if signing_key_b64:
        try:
            seed = base64.b64decode(signing_key_b64.strip())
            receipt = sign_receipt(receipt, SigningKey(seed[:32]))
        except Exception:
            pass

    receipt_out_dir = Path("artifacts/receipts") / village_id
    receipt_out = receipt_out_dir / f"policy_pull.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.{chosen.policy_hash[:12]}.json"
    write_receipt(receipt_out, receipt)
    typer.echo(f"Wrote {receipt_out}")

    out_dir = Path("artifacts/policy_feed") / village_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"latest.{chosen.policy_hash}.json"
    out.write_text(chosen.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote {out}")
    if manifest is not None:
        man_out = out_dir / f"manifest.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        man_out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        typer.echo(f"Wrote {man_out}")



@norms.command("init")
def norms_init(village_id: str, out: Path, title: str = None, author: str = "operator"):
    norm_set = init_norm_set(village_id=village_id, title=title, author=author)
    write_norm_json(out, norm_set)
    typer.echo(f"Wrote {out}")


@norms.command("validate")
def norms_validate(inp: Path):
    norm_set = validate_norm_file(inp)
    typer.echo(f"OK norm_set_id={norm_set.norm_set_id} norms={len(norm_set.norms)}")


@norms.command("compile")
def norms_compile(inp: Path, out: Path):
    try:
        norm_set = validate_norm_file(inp)
        result = compile_norm_set(norm_set)
    except ContradictoryNormError as exc:
        typer.echo(f"Compilation failed: {exc}", err=True)
        raise typer.Exit(code=1)
    write_norm_json(out, result.artifact)
    typer.echo(f"Wrote {out}")


@norms.command("diff")
def norms_diff(old: Path, new: Path):
    old_set = validate_norm_file(old)
    new_set = validate_norm_file(new)
    typer.echo(json.dumps(diff_norm_sets(old_set, new_set), indent=2, ensure_ascii=False))


@policy.command("quorum-inspect")
def policy_quorum_inspect(village_id: str, data_root: Path = Path("data"), out: Path = typer.Option(None, help="Optional JSON report output path")):
    """Inspect the effective policy quorum configuration for a village."""
    if load_village is None:
        typer.echo("Local village loader not available", err=True)
        raise typer.Exit(code=2)

    village = load_village(data_root, village_id)
    policy_obj = village.policy.model_dump()
    quorum_cfg = policy_obj.get("policy_quorum") or {}
    allowlist = list(policy_obj.get("policy_signer_allowlist") or [])
    weights = dict(policy_obj.get("policy_signer_weights") or {})
    roles = dict(policy_obj.get("policy_signer_roles") or {})

    model = quorum_cfg.get("model") or ("m_of_n" if policy_obj.get("require_policy_signature") else "optional")
    payload = {
        "village_id": village_id,
        "inspected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "require_policy_signature": bool(policy_obj.get("require_policy_signature", False)),
        "model": model,
        "threshold_m": quorum_cfg.get("threshold_m") or policy_obj.get("policy_signature_threshold_m") or 1,
        "threshold_weight": quorum_cfg.get("threshold_weight"),
        "role_requirements": quorum_cfg.get("role_requirements") or [],
        "allowlisted_signer_count": len(allowlist),
        "allowlisted_signers": allowlist,
        "weighted_signers": weights,
        "role_assignments": roles,
    }

    if out is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = Path("artifacts/quorum") / village_id / f"quorum.{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    typer.echo(json.dumps(payload, indent=2))
    typer.echo(f"Wrote {out}")


@policy.command("apply-compiled")
def policy_apply_compiled(inp: Path, village_id: str = None, actor: str = "norm-compiler", data_root: Path = Path("data")):
    artifact = CompiledPolicyArtifact.model_validate_json(inp.read_text(encoding="utf-8"))
    if village_id and artifact.village_id != village_id:
        typer.echo(f"Village mismatch: artifact={artifact.village_id} arg={village_id}", err=True)
        raise typer.Exit(code=1)
    apply_compiled_policy(data_root, artifact, actor=actor)
    typer.echo(f"Applied compiled policy for {artifact.village_id}")


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
def registry_export(village_id: str, out: Path = typer.Option(Path("registry_export.json"), help="Output JSON file"), authority: str = typer.Option("local-operator")):
    """Export a versioned registry interchange artifact with provenance."""
    from .validate import validate_village_id
    from .villages import load_village, _members_path, _revocations_path
    from .trust_anchors import iter_anchor_entries
    from .registry_interop import ExternalRegistryArtifact
    validate_village_id(village_id)
    root = Path("data")
    v = load_village(root, village_id)
    members = _members_path(root, village_id).read_text(encoding="utf-8").splitlines()
    revocations = _revocations_path(root, village_id).read_text(encoding="utf-8").splitlines()
    anchors = [a.model_dump(mode="json") for a in iter_anchor_entries(root, village_id)]
    payload = ExternalRegistryArtifact(
        registry_id=f"policymesh:{village_id}", village_id=village_id, authority=authority,
        policy=v.policy.model_dump(), members=[m for m in members if m.strip()],
        revocations=[r for r in revocations if r.strip()], trust_anchors=anchors,
        provenance={"source": "PolicyMesh", "mode": "export"},
    )
    out.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(str(out))


@registry.command("validate")
def registry_validate(path: Path):
    """Validate a registry artifact without mutating local authoritative state."""
    from .registry_interop import ExternalRegistryArtifact
    artifact = ExternalRegistryArtifact.model_validate_json(path.read_text(encoding="utf-8"))
    typer.echo(json.dumps({"valid": True, "registry_id": artifact.registry_id, "village_id": artifact.village_id}, indent=2))


@registry.command("diff")
def registry_diff(path: Path):
    """Compare an incoming registry artifact with local state."""
    from .registry_interop import ExternalRegistryArtifact, compare_registry
    from .villages import load_village
    artifact = ExternalRegistryArtifact.model_validate_json(path.read_text(encoding="utf-8"))
    try:
        local = load_village(Path("data"), artifact.village_id).policy.model_dump()
    except Exception:
        local = {}
    typer.echo(json.dumps(compare_registry(local, artifact), indent=2))


@registry.command("import")
def registry_import(path: Path, decision: str = typer.Option("defer", help="defer|apply|reject")):
    """Validate and explicitly decide an import; never silently overwrite local authority."""
    from .registry_interop import ExternalRegistryArtifact, compare_registry
    from .villages import load_village, save_village, Village, VillagePolicy
    artifact = ExternalRegistryArtifact.model_validate_json(path.read_text(encoding="utf-8"))
    if decision not in {"defer", "apply", "reject"}:
        raise typer.BadParameter("decision must be defer, apply, or reject")
    try:
        local_policy = load_village(Path("data"), artifact.village_id).policy.model_dump()
    except Exception:
        local_policy = {}
    report = compare_registry(local_policy, artifact)
    receipt = {**report, "decision": decision, "source": str(path), "decided_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    out = Path("artifacts/registry_import") / artifact.village_id
    out.mkdir(parents=True, exist_ok=True)
    receipt_path = out / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.{decision}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if decision == "apply":
        try:
            existing = load_village(Path("data"), artifact.village_id)
            updated = existing.model_copy(update={"policy": VillagePolicy.model_validate(artifact.policy)})
            save_village(Path("data"), updated)
        except Exception:
            typer.echo("apply requires an existing local village; import refused", err=True)
            raise typer.Exit(code=1)
    typer.echo(json.dumps(receipt, indent=2))
    typer.echo(f"Wrote {receipt_path}")


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

# -----------------------------
# Governed lifecycle operations
# -----------------------------
@policy.command("transition")
def policy_transition(
    inp: Path,
    to_state: str = typer.Option(..., help="approved|active|rolled_back"),
    out: Path = typer.Option(..., help="Output update artifact"),
    actor: str = typer.Option("operator"),
    reason: str = typer.Option(""),
    rollback_to: str = typer.Option("", help="Required when transitioning to rolled_back"),
):
    """Perform a validated lifecycle transition and emit a durable transition event."""
    from .policy_lifecycle import transition_update, write_lifecycle_event
    u = VillagePolicyUpdate.model_validate_json(inp.read_text(encoding="utf-8"))
    try:
        changed, event = transition_update(
            u, to_state, actor=actor, reason=reason or None,
            rollback_to_policy_hash=rollback_to or None,
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(changed.model_dump_json(indent=2), encoding="utf-8")
    ev = write_lifecycle_event(Path("."), event)
    typer.echo(f"Wrote {out}")
    typer.echo(f"Wrote {ev}")


@policy.command("rollback")
def policy_rollback(
    village_id: str,
    target_policy_hash: str,
    actor: str = typer.Option("operator"),
    data_root: Path = typer.Option(Path("data")),
):
    """Restore a historical policy as a new audited governance act; history is never erased."""
    from .villages import load_village, apply_policy_update, policy_history_path
    from .policy_lifecycle import find_policy_in_history
    from .policy_updates import compute_policy_hash
    validate_village_id(village_id)
    current = load_village(data_root, village_id)
    hp = policy_history_path(data_root, village_id)
    rows = [json.loads(line) for line in hp.read_text(encoding="utf-8").splitlines() if line.strip()] if hp.exists() else []
    target = find_policy_in_history(rows, target_policy_hash)
    if target is None:
        typer.echo("target policy hash not found in local history", err=True)
        raise typer.Exit(code=1)
    previous = compute_policy_hash(current.policy.model_dump())
    apply_policy_update(data_root, village_id, target, actor=actor, update_meta={
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "policy_update": "rollback",
        "policy_hash": target_policy_hash,
        "previous_policy_hash": previous,
        "rollback_to_policy_hash": target_policy_hash,
    })
    typer.echo(json.dumps({"village_id": village_id, "previous_policy_hash": previous, "active_policy_hash": target_policy_hash, "action": "rollback"}, indent=2))


# -----------------------------
# Trust anchor operator surface
# -----------------------------
def _anchor_key_hash(public_key_b64: str) -> str:
    from .policy_updates import key_hash_from_public_key_b64
    return key_hash_from_public_key_b64(public_key_b64)


@anchors.command("register")
def anchor_register(village_id: str, public_key: str, anchor_id: str, actor: str = "operator", reason: str = "register"):
    from .trust_anchors import store_anchor_entry
    entry = TrustAnchorEntry(village_id=village_id, created_at=datetime.now(timezone.utc), actor=actor, action="register", anchor_id=anchor_id, anchor_public_key=public_key, anchor_key_hash=_anchor_key_hash(public_key), reason=reason)
    try:
        from .keys import load_signing_key_from_env
        entry = add_anchor_signature(entry, load_signing_key_from_env())
    except Exception:
        pass
    path = store_anchor_entry(Path("data"), entry)
    typer.echo(str(path))


@anchors.command("rotate")
def anchor_rotate(village_id: str, public_key: str, anchor_id: str, previous_key_hash: str, actor: str = "operator", reason: str = "rotation"):
    from .trust_anchors import store_anchor_entry
    entry = TrustAnchorEntry(village_id=village_id, created_at=datetime.now(timezone.utc), actor=actor, action="rotate", anchor_id=anchor_id, anchor_public_key=public_key, anchor_key_hash=_anchor_key_hash(public_key), previous_anchor_key_hash=previous_key_hash, reason=reason)
    try:
        from .keys import load_signing_key_from_env
        entry = add_anchor_signature(entry, load_signing_key_from_env())
    except Exception:
        pass
    path = store_anchor_entry(Path("data"), entry)
    typer.echo(str(path))


@anchors.command("revoke")
def anchor_revoke(village_id: str, anchor_id: str, anchor_key_hash: str, actor: str = "operator", reason: str = "revoked"):
    from .trust_anchors import store_anchor_entry
    entry = TrustAnchorEntry(village_id=village_id, created_at=datetime.now(timezone.utc), actor=actor, action="revoke", anchor_id=anchor_id, anchor_key_hash=anchor_key_hash, reason=reason)
    try:
        from .keys import load_signing_key_from_env
        entry = add_anchor_signature(entry, load_signing_key_from_env())
    except Exception:
        pass
    path = store_anchor_entry(Path("data"), entry)
    typer.echo(str(path))


@anchors.command("history")
def anchor_history(village_id: str):
    from .trust_anchors import iter_anchor_entries
    rows = [x.model_dump(mode="json") for x in iter_anchor_entries(Path("data"), village_id)]
    typer.echo(json.dumps(rows, indent=2))


@anchors.command("inspect")
def anchor_inspect(village_id: str):
    from .trust_anchors import latest_active_anchor
    entry = latest_active_anchor(Path("data"), village_id)
    if not entry:
        typer.echo("no active anchor")
        raise typer.Exit(code=2)
    typer.echo(entry.model_dump_json(indent=2))


# -----------------------------
# Evidence bundle operations
# -----------------------------
evidence = typer.Typer(help="Assemble and verify portable policy evidence bundles.")
app.add_typer(evidence, name="evidence")


@evidence.command("build")
def evidence_build(village_id: str, event_id: str, source: List[Path] = typer.Option(..., "--source"), out: Path = Path("artifacts/evidence"), actor: str = "operator"):
    from .evidence_bundle import build_evidence_bundle
    bundle = build_evidence_bundle(out, event_id=event_id, village_id=village_id, sources=source, actor=actor)
    typer.echo(str(bundle))


@evidence.command("verify")
def evidence_verify(path: Path):
    from .evidence_bundle import verify_evidence_bundle
    ok, errors = verify_evidence_bundle(path)
    typer.echo(json.dumps({"valid": ok, "errors": errors}, indent=2))
    raise typer.Exit(code=0 if ok else 1)


# -----------------------------
# Crypto lifecycle inspection
# -----------------------------
crypto_policy_cli = typer.Typer(help="Inspect governed cryptographic algorithm policy.")
app.add_typer(crypto_policy_cli, name="crypto-policy")


@crypto_policy_cli.command("show")
def crypto_policy_show():
    from .crypto_policy import CryptographicPolicy
    typer.echo(CryptographicPolicy().model_dump_json(indent=2))
