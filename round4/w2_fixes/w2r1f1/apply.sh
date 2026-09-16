#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import csv, json, os
R = os.environ["ROUND4_ROOT"]
rows = list(csv.DictReader(open(R + "/input/spawn_window_127.csv")))
CANNED = "b4aefd29108f232f9c0d5a4b030215c1"
by_parent = {}
refused = 0
for r in rows:
    p = r["parent"][:8]
    d = by_parent.setdefault(p, {"n": 0, "refused": 0})
    d["n"] += 1
    if r["fr_md5"] == CANNED:
        d["refused"] += 1
        refused += 1
n = len(rows)
fresh = [r["sid"] for r in rows if r["sid"] >= "433"]
fresh_genuine = [r["sid"] for r in rows if r["sid"] >= "433" and r["fr_md5"] != CANNED]
out = {"window": "spawn_id>312", "n": n, "refused": refused,
       "refusal_rate": round(refused / n, 4),
       "by_parent": [{"parent": k, "n": v["n"], "refused": v["refused"],
                      "rate": round(v["refused"] / v["n"], 3)} for k, v in sorted(by_parent.items())],
       "fresh_tail_sids": fresh, "fresh_genuine_sids": fresh_genuine,
       "source": "muse.db 2026-09-16, programmatic rebuild (wave-1 hand transcription had an error)"}
json.dump(out, open(R + "/rounds/w2_aggregates.json", "w"), indent=1)
print("rebuilt: n=%d refused=%d rate=%.4f fresh_genuine=%s" % (n, refused, refused / n, fresh_genuine))
PYEOF
