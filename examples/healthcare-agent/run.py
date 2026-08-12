#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from examples._shared.personal_agent_demo import run_example, scenario_names
EXAMPLE = Path(__file__).resolve().parent
SCENARIOS = scenario_names(EXAMPLE)
TITLE = "Healthcare Appointment & Consent Demo"
def main():
    parser=argparse.ArgumentParser(description="Run the PolicyMesh healthcare appointment and consent reference example")
    parser.add_argument("scenario", nargs="?", default="appointment-permitted", choices=SCENARIOS+["all"])
    args=parser.parse_args()
    if args.scenario=="all":
        return 1 if sum(run_example(EXAMPLE,TITLE,s) for s in SCENARIOS) else 0
    return run_example(EXAMPLE,TITLE,args.scenario)
if __name__=="__main__": raise SystemExit(main())
