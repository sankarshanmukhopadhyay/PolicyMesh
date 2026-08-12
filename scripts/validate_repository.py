#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import sys
import re

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md", "ROADMAP.md", "PROJECT-STATUS.yaml", "GOVERNANCE.md", "SECURITY.md",
    "CODE_OF_CONDUCT.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE",
    "assurance/controls.yaml", "assurance/capability-control-map.yaml", "assurance/evidence-map.yaml",
    "schemas/external_registry.schema.json", "schemas/project-status.schema.json", "schemas/action_policy.schema.json", "schemas/action_decision_receipt.schema.json", "config/profiles/development.yaml",
    "config/profiles/federation-pilot.yaml", "config/profiles/production-hardened.yaml",
]

def main() -> int:
    checks = []
    for rel in REQUIRED:
        exists = (ROOT / rel).exists()
        checks.append({"check": f"required:{rel}", "pass": exists})
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    checks.append({"check": "roadmap:no-partial-status", "pass": "**Status:** 🟡 Partial" not in roadmap})
    status = (ROOT / "PROJECT-STATUS.yaml").read_text(encoding="utf-8")
    for token in ["maturity:", "lifecycle:", "operational_status:", "normative_scope:", "does_not_own:", "validation_commands:"]:
        checks.append({"check": f"project-status:{token}", "pass": token in status})
    try:
        status_obj = yaml.safe_load(status)
        status_schema = json.loads((ROOT / "schemas" / "project-status.schema.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(status_schema).iter_errors(status_obj))
        checks.append({"check": "project-status:schema", "pass": not errors, "errors": [e.message for e in errors]})
    except Exception as exc:
        checks.append({"check": "project-status:schema", "pass": False, "errors": [str(exc)]})
    try:
        for schema_name in ["action_policy.schema.json", "action_decision_receipt.schema.json"]:
            schema_obj = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema_obj)
            checks.append({"check": f"schema:{schema_name}:valid", "pass": True})
    except Exception as exc:
        checks.append({"check": "action-schemas:valid", "pass": False, "errors": [str(exc)]})
    try:
        registry_schema = json.loads((ROOT / "schemas" / "external_registry.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(registry_schema)
        checks.append({"check": "external-registry:schema-valid", "pass": True})
    except Exception as exc:
        checks.append({"check": "external-registry:schema-valid", "pass": False, "errors": [str(exc)]})
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in ["What PolicyMesh solves", "Authority boundary", "First result", "How to adopt PolicyMesh", "Evidence", "Project status"]:
        checks.append({"check": f"readme:{heading}", "pass": heading in readme})
    broken_links = []
    for md in ROOT.rglob("*.md"):
        if "upstream" in md.parts:
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            target = target.split("#", 1)[0].strip().split(' "', 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            dest = (md.parent / target).resolve()
            try:
                dest.relative_to(ROOT.resolve())
            except ValueError:
                continue
            if not dest.exists():
                broken_links.append({"source": str(md.relative_to(ROOT)), "target": target})
    checks.append({"check": "documentation:internal-links", "pass": not broken_links, "broken": broken_links})

    result = {"format": "policymesh.repository-validation.v1", "passed": all(c["pass"] for c in checks), "checks": checks}
    out = ROOT / "artifacts" / "validation" / "validation-results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
