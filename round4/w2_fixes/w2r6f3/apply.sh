#!/bin/bash
set -uo pipefail

hdr=$(head -1 "$ROUND4_ROOT/input/snapshot_new.csv")
python3 - "$hdr" <<'PYEOF'
import csv, os, sys
R = os.environ["ROUND4_ROOT"]
hdr = sys.argv[1].split(",")
rows = [r for r in csv.DictReader(open(R + "/input/spawn_window_127.csv")) if r["sid"] == "432"]
with open(R + "/rounds/w2_feed_snapshot.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(hdr)
    for r in rows:
        rec = {"spawn_id": r["sid"], "parent_agent_id": r["parent"], "status": r["status"],
               "fr_md5": r["fr_md5"], "fr_len": r["fr_len"], "created_epoch": ""}
        w.writerow([rec.get(c, "") for c in hdr])
print("snapshot rows:", len(rows))
PYEOF
bash "$HOME/workspace/refusal-hunt/canary-feed.sh" "$ROUND4_ROOT/rounds/w2_feed_snapshot.csv" 2>&1 | tail -2
date +%s > "$ROUND4_ROOT/input/w2_feed_ts.txt"
