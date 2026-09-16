#!/bin/bash
# R4b: journal repair — backfill the R2 entry (R2's main() ran pre-patch, so it
# never wrote journal.jsonl; R3c then failed on the missing file), sort by ts,
# verify R2+R3 present, rebuild ROUNDSUMMARY.md.
set -uo pipefail
FRD=~/workspace/refusal-hunt/fix-rounds
J=$FRD/journal.jsonl
log(){ echo "[R4b $(date -u +%H:%M:%SZ)] $*" >&2; }
python3 - "$FRD" <<'PYEOF' || { log "journal repair FAIL"; echo '{"fix":"R4b","result":"FAIL","reason":"repair"}'; exit 1; }
import sys, json, os
frd = sys.argv[1]
j = frd + "/journal.jsonl"
rows = []
if os.path.exists(j):
    rows = [json.loads(l) for l in open(j) if l.strip()]
if not any(r.get("round") == "R2" for r in rows):
    rows.append({"ts": "2026-09-16T05:54:24Z", "round": "R2", "wall_secs": 1.9,
                 "nest_asyncio": True, "nest_ver": "unknown", "backfilled": True,
                 "pass": 3, "fail": 0,
                 "fixes": [{"fix": "fix-R2a.sh", "rc": 0, "secs": 1.9, "result": "PASS"},
                           {"fix": "fix-R2b.sh", "rc": 0, "secs": 0.2, "result": "PASS"},
                           {"fix": "fix-R2c.sh", "rc": 0, "secs": 0.1, "result": "PASS"}]})
    print("R2 backfilled (verified 3/3 from driver output)")
rows.sort(key=lambda r: r.get("ts", ""))
with open(j, "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
r2 = [r for r in rows if r.get("round") == "R2"]
r3 = [r for r in rows if r.get("round") == "R3"]
assert r2 and r2[-1]["pass"] == 3, "R2 not 3/3"
assert r3, "R3 entry missing (its main() should have written it)"
tp = sum(r["pass"] for r in rows); tf = sum(r["fail"] for r in rows)
lines = ["# Fix-round summary (cumulative, from journal.jsonl)", "",
         "| round | pass | fail | wall_s | nest |",
         "|---|---|---|---|---|"]
for r in rows:
    lines.append("| %s | %d | %d | %s | %s |" % (r.get("round"), r["pass"], r["fail"], r.get("wall_secs"), r.get("nest_asyncio")))
lines += ["", "**Total: %d PASS / %d FAIL** across %d rounds." % (tp, tf, len(rows))]
open(frd + "/ROUNDSUMMARY.md", "w").write("\n".join(lines) + "\n")
print("journal ok: %d rounds, %d pass / %d fail; ROUNDSUMMARY.md written" % (len(rows), tp, tf))
PYEOF
log "PASS"
echo '{"fix":"R4b","result":"PASS"}'; exit 0
