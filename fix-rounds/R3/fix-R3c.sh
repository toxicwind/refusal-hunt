#!/bin/bash
# R3c: journal verification + cumulative ROUNDSUMMARY.md build from journal.jsonl.
set -uo pipefail
FRD=~/workspace/refusal-hunt/fix-rounds
log(){ echo "[R3c $(date -u +%H:%M:%SZ)] $*" >&2; }
[ -f "$FRD/journal.jsonl" ] || { log "journal.jsonl missing"; echo '{"fix":"R3c","result":"FAIL","reason":"no-journal"}'; exit 1; }
python3 - "$FRD" <<'PYEOF' || { echo '{"fix":"R3c","result":"FAIL","reason":"verify"}'; exit 1; }
import sys, json
frd = sys.argv[1]
rows = [json.loads(l) for l in open(frd + "/journal.jsonl") if l.strip()]
assert rows, "journal empty"
r2 = [r for r in rows if r.get("round") == "R2"]
assert r2 and r2[-1]["pass"] == 3 and r2[-1]["fail"] == 0, "R2 not 3/3 in journal"
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
echo '{"fix":"R3c","result":"PASS"}'; exit 0
