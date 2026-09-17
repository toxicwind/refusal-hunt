#!/usr/bin/env python3
"""Write rounds_manifest.runtime.json — the manifest with agent-executed
db-fix annotations.

db-kind fixes need a live agent; the runner cannot spawn one during a
refusal storm. This script merges db_fix_evidence.json (agent-executed
results) into the manifest so the runner can mark those fixes PASS with
agent_confirmed=true. Fixes without evidence stay as-is (the runner will
record them as FAIL/REDIRECTED honestly).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "rounds_manifest.json")
EV = os.path.join(HERE, "db_fix_evidence.json")
OUT = os.path.join(HERE, "rounds_manifest.runtime.json")


def main():
    with open(SRC) as f:
        manifest = json.load(f)
    evidence = json.load(open(EV)) if os.path.exists(EV) else {}
    annotated = []
    for rnd in manifest["rounds"]:
        for fix in rnd["fixes"]:
            fid = fix.get("id")
            if fid in evidence:
                e = evidence[fid]
                fix["agent_done"] = True
                fix["agent_executed_ts"] = e.get("ts")
                fix["result"] = json.dumps(e["result"], default=str)[:1500]
                v = fix.get("verify")
                if isinstance(v, dict):
                    v["agent_confirmed"] = True
                annotated.append(fid)
    with open(OUT, "w") as f:
        json.dump(manifest, f, indent=1)
    print(json.dumps({"runtime_manifest": OUT, "annotated": annotated}))


if __name__ == "__main__":
    main()
