#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
H = os.path.expanduser("~")
# fix -> (artifact path, legit_if: later passing fix recreated it)
TABLE = {
    "r1f2": (H + "/bin/pkill-guard", "w2r1f2"),
    "r2f2": (R + "/rounds/r2_gate.json", None),
    "r4f1": (R + "/rounds/r4_coverage.json", None),
    "r4f2": (R + "/rounds/r4_gate_timeline.json", None),
    "r6f3": (R + "/rounds/r6_dbsweep.json", None),
    "r7f1": (H + "/sdk/go/bin/go", "w2r3f1"),
    "r8f2": (R + "/dashboard.html", "post-phase"),
}
status = {}
for line in open(R + "/rounds_results.jsonl"):
    d = json.loads(line)
    if d.get("wave") == 2 and d.get("id"):
        status[d["id"]] = d["status"]
residues = []
for fid, (path, legit) in TABLE.items():
    exists = os.path.lexists(path)
    legit_now = (legit == "post-phase") or (legit and status.get(legit) == "pass")
    if exists and not legit_now:
        residues.append({"fix": fid, "path": path})
    print("%s exists=%s legit=%s" % (fid, exists, legit_now))
# r6f2 special: function must be present iff w2r2f3 passed (it re-appends)
guard = open(os.path.expanduser("~/workspace/refusal-hunt/round3/spawn_guard.py")).read()
has_fn = "def verify_spawn_record" in guard
if has_fn and status.get("w2r2f3") != "pass":
    residues.append({"fix": "r6f2", "path": "spawn_guard.py:verify_spawn_record"})
out = {"residues": residues, "clean": not residues}
json.dump(out, open(R + "/rounds/w2_rollback_audit.json", "w"), indent=1)
print("rollback audit clean=%s residues=%d" % (out["clean"], len(residues)))
PYEOF
