#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import os
p = os.path.expanduser("~/workspace/watchdog-supervisor.sh")
s = open(p).read()
if "R4-STAGING" in s:
    print("already staged"); raise SystemExit(0)
anchor = 'log_alert "CANARY_STARVED log.jsonl stale ${STALE_FOR}s (>45min) :: run: ~/workspace/refusal-hunt/canary-feed.sh <snapshot.csv>"'
assert anchor in s, "anchor not found"
block = anchor + "\n" + """          # R4-STAGING: stage a ready-to-run feed bundle for the next live session.
          STAGE_DIR="$HOME/workspace/refusal-hunt/round4/pending_feed"
          mkdir -p "$STAGE_DIR" && date -u +%Y-%m-%dT%H:%M:%SZ > "$STAGE_DIR/starved_at"
          cat > "$STAGE_DIR/next_snapshot_query.sql" <<'SQLEOF'
SELECT spawn_id, status, md5(final_response) AS fr_md5,
       length(final_response) AS fr_len, created_at AS created_epoch
FROM agent.subagent_spawns WHERE spawn_id > 432 ORDER BY spawn_id
SQLEOF"""
s = s.replace(anchor, block)
open(p, "w").write(s)
print("patched supervisor")
PYEOF
