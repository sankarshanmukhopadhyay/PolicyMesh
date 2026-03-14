from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Dict, Tuple

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from nacl.signing import SigningKey

from .policy_feed import (
    build_policy_feed_manifest,
    filter_updates_since,
    get_policy_update_by_hash,
    latest_policy_update,
    paginate_updates,
    sign_manifest,
    signer_allowed,
    store_policy_update,
)
from .policy_updates import VillagePolicyUpdate, build_update
from .validate import validate_village_id
from .audit_export import export_audit_json, export_audit_csv, sign_digest_hex
from .keys import load_signing_key_from_env
from .file_lock import locked_open

# Optional: if a richer villages module exists, use it for auth + apply + policy lookup.
try:
    from .villages import authorize, role_can, load_village, apply_policy_update  # type: ignore
except Exception:  # pragma: no cover
    authorize = None
    role_can = None
    load_village = None
    apply_policy_update = None


def _bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def create_app(store_root: Path = Path("data/store"), villages_root: Path = Path("data")) -> FastAPI:
    app = FastAPI(title="Links Claim Exchange", version="0.12.0")

    # Simple in-memory per-village rate limiter (minute bucket).
    # NOTE: In production, put Links behind a proper gateway (Envoy/Nginx) with real rate limiting.
    _buckets: Dict[Tuple[str, str], Tuple[int, int]] = {}  # (village_id, client_key) -> (minute_epoch, count)

    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        path = request.url.path or ""
        # Only apply rate limiting to village-scoped routes.
        if path.startswith("/villages/"):
            parts = path.split("/")
            if len(parts) >= 3:
                village_id = parts[2]
                try:
                    validate_village_id(village_id)
                except Exception:
                    raise HTTPException(status_code=400, detail="invalid village_id")

                limit = 60
                if load_village:
                    try:
                        v = load_village(villages_root, village_id)
                        limit = int(getattr(v, "policy").rate_limit_per_min)  # type: ignore[attr-defined]
                    except Exception:
                        # Fail open to avoid breaking local/dev deployments.
                        limit = 60

                client_host = request.client.host if request.client else "unknown"
                client_key = client_host

                minute = int(time.time() // 60)
                k = (village_id, client_key)
                m0, c0 = _buckets.get(k, (minute, 0))
                if m0 != minute:
                    m0, c0 = minute, 0
                c0 += 1
                _buckets[k] = (m0, c0)

                # Opportunistic cleanup to keep memory bounded.
                if len(_buckets) > 5000:
                    cutoff = minute - 5
                    for kk, (mm, _) in list(_buckets.items()):
                        if mm < cutoff:
                            _buckets.pop(kk, None)

                if c0 > max(1, limit):
                    raise HTTPException(status_code=429, detail="rate limit exceeded")
        return await call_next(request)

    @app.get("/villages/{village_id}/policy/latest")
    def policy_latest(village_id: str):
        validate_village_id(village_id)
        u = latest_policy_update(villages_root, village_id)
        if not u:
            raise HTTPException(status_code=404, detail="no policy updates")
        return json.loads(u.model_dump_json())

    @app.get("/villages/{village_id}/policy/updates")
    def policy_updates(village_id: str, since: str | None = Query(default=None)):
        validate_village_id(village_id)
        ups = filter_updates_since(villages_root, village_id, since_hash=since)
        return [json.loads(u.model_dump_json()) for u in ups]

    @app.get("/villages/{village_id}/policy/by_hash/{policy_hash}")
    def policy_update_by_hash(village_id: str, policy_hash: str):
        validate_village_id(village_id)
        u = get_policy_update_by_hash(villages_root, village_id, policy_hash)
        if not u:
            raise HTTPException(status_code=404, detail="policy update not found")
        return json.loads(u.model_dump_json())

    @app.get("/villages/{village_id}/policy/updates_page")
    def policy_updates_page(
        village_id: str,
        since: str | None = Query(default=None),
        cursor: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
    ):
        """Paginated policy updates (envelope). Cursor is the last policy_hash from the previous page."""
        validate_village_id(village_id)
        ups = filter_updates_since(villages_root, village_id, since_hash=since)
        items, next_cursor = paginate_updates(ups, cursor=cursor, limit=limit)
        return {
            "village_id": village_id,
            "since": since,
            "cursor": cursor,
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [json.loads(u.model_dump_json()) for u in items],
        }

    @app.get("/villages/{village_id}/policy/manifest")
    def policy_manifest(village_id: str):
        """Signed policy feed manifest with integrity metadata (merkle root + hash chain head)."""
        validate_village_id(village_id)
        m = build_policy_feed_manifest(villages_root, village_id)

        # Optional node signing key (base64 seed). If present, manifests are signed.
        sk_b64 = os.environ.get("LINKS_NODE_SIGNING_KEY_B64")
        if sk_b64:
            try:
                seed = base64.b64decode(sk_b64.strip(), validate=True)
                if len(seed) < 32:
                    raise ValueError("seed too short")
                sk = SigningKey(seed[:32])
                m = sign_manifest(m, sk)
            except Exception:
                # Fail open (manifest still returned unsigned) to avoid breaking dev deployments.
                pass

        return json.loads(m.model_dump_json())

    @app.post("/villages/{village_id}/policy")
    def policy_update(village_id: str, body: dict, authorization: str | None = Header(default=None)):
        validate_village_id(village_id)

        # If auth system exists, require manage permission.
        if authorize and role_can and load_village:
            token = _bearer_token(authorization)
            member = authorize(villages_root, village_id, token) if token else None
            if not member:
                raise HTTPException(status_code=403, detail="forbidden")
            v = load_village(villages_root, village_id)
            if not role_can(v.policy, member.get("role", "observer"), "manage"):
                raise HTTPException(status_code=403, detail="forbidden")
            current_policy = v.policy.model_dump()
            actor = member.get("member_id")
        else:
            # local/dev mode
            current_policy = {}
            actor = "local"

        # Accept either signed update artifact or raw policy dict
        try:
            u = VillagePolicyUpdate.model_validate(body)
        except Exception:
            policy_obj = body.get("policy") if isinstance(body, dict) and "policy" in body else body
            u = build_update(village_id=village_id, policy=policy_obj, actor=actor)

        ok, msg = signer_allowed(current_policy, u)
        if not ok:
            raise HTTPException(status_code=400, detail=f"policy update rejected: {msg}")

        store_policy_update(villages_root, u)

        # Apply locally if the implementation supports it
        if apply_policy_update:
            apply_policy_update(
                villages_root,
                village_id,
                u.policy,
                actor=actor,
                update_meta={"policy_hash": u.policy_hash, "policy_update": "stored"},
            )
        return {"status": "ok", "village_id": village_id, "policy_hash": u.policy_hash}

    

    @app.get("/public/villages/{village_id}/policy/latest")
    def public_latest_policy(village_id: str):
        """Unauthenticated read-only policy endpoint (opt-in)."""
        validate_village_id(village_id)
        env_ok = os.environ.get("LINKS_PUBLIC_POLICY", "").strip().lower() in {"1", "true", "yes"}
        per_village_ok = False
        if load_village is not None:
            try:
                v = load_village(villages_root, village_id)
                per_village_ok = bool(getattr(v.policy, "public_policy_endpoint", False)) or getattr(v.policy, "visibility", "private") == "public"
            except Exception:
                per_village_ok = False
        if not (env_ok or per_village_ok):
            raise HTTPException(status_code=404, detail="public policy endpoint not enabled")
        u = latest_policy_update(store_root, village_id)
        if not u:
            raise HTTPException(status_code=404, detail="no policy updates found")
        return u.model_dump()

    @app.get("/villages/{village_id}/transparency/policy_log")
    def transparency_policy_log(village_id: str, limit: int = Query(default=500, ge=1, le=5000)):
        """Return recent transparency log entries (JSONL)."""
        validate_village_id(village_id)
        p = store_root / "transparency" / village_id / "policy_log.jsonl"
        if not p.exists():
            raise HTTPException(status_code=404, detail="no transparency log")

        def _iter():
            with locked_open(p, "r") as f:
                lines = f.readlines()
            for line in lines[-limit:]:
                yield line

        return StreamingResponse(_iter(), media_type="application/x-ndjson")

    @app.get("/villages/{village_id}/audit/export")
    def audit_export(village_id: str, fmt: str = Query(default="json", pattern="^(json|csv)$"), sign: bool = Query(default=True)):
        """Export audit log for a village (best-effort filter) with optional digest signing."""
        validate_village_id(village_id)
        audit_path = store_root / "audit" / "audit.log.jsonl"
        if not audit_path.exists():
            raise HTTPException(status_code=404, detail="no audit log")
        out_dir = store_root / "audit" / "exports" / village_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"audit.{fmt}"
        tmp = out_dir / "audit.filtered.jsonl"
        with locked_open(audit_path, "r") as f_in, locked_open(tmp, "w") as f_out:
            for line in f_in:
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if ev.get("village_id") == village_id:
                    f_out.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")
        if fmt == "json":
            digest, count = export_audit_json(tmp, out_path)
        else:
            digest, count = export_audit_csv(tmp, out_path)
        sig_hex = None
        if sign:
            try:
                sk = load_signing_key_from_env()
                sig_hex = sign_digest_hex(digest, sk)
                (out_path.with_suffix(out_path.suffix + ".sha256")).write_text(digest + "\n", encoding="utf-8")
                (out_path.with_suffix(out_path.suffix + ".sighex")).write_text(sig_hex + "\n", encoding="utf-8")
            except Exception:
                pass
        return {"village_id": village_id, "format": fmt, "count": count, "sha256": digest, "signed": bool(sig_hex)}

    return app
