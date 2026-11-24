"""Execute the actual conformance tests and retain their outcome (including failures)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
from importlib.metadata import version

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/validation"
OUT.mkdir(parents=True, exist_ok=True)
xml = OUT / "action-conformance.xml"
xml.unlink(missing_ok=True)
proc = subprocess.run([sys.executable, "-m", "pytest", "tests/test_action_conformance.py",
                       "tests/test_action_hardening.py", "tests/test_action_verification.py",
                       "--junitxml", str(xml)], cwd=ROOT)
rows = []
if xml.exists():
    for case in ET.parse(xml).iter("testcase"):
        state = "fail" if case.find("failure") is not None or case.find("error") is not None else "not_checked" if case.find("skipped") is not None else "pass"
        rows.append({"id":case.attrib["name"], "suite":case.attrib["classname"], "result":state})
commit = os.environ.get("GITHUB_SHA") or subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
passed = proc.returncode == 0 and bool(rows) and all(r["result"]=="pass" for r in rows)
report = {"format":"policymesh.action_conformance.v1","evaluation_semantics":"policymesh.action_evaluation.v2",
          "implementation_version":version("links"),"source_commit":commit,"passed":passed,"cases":rows}
(OUT / "action-conformance-results.json").write_text(json.dumps(report,indent=2)+"\n")
sys.exit(0 if passed else 1)
