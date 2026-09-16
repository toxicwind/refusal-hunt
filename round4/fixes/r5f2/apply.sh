#!/bin/bash
set -uo pipefail

MTIME=$(python3 "$HOME/workspace/skills/awrawr-mcp/bin/exec.py" --timeout 15 'stat -c %Y /home/toxic/refusal-hunt/canary/log.jsonl' 2>/dev/null | tail -1)
FED_AT=$(cat "$ROUND4_ROOT/input/feed_ts.txt" 2>/dev/null || echo 0)
python3 - "$MTIME" "$FED_AT" <<'PYEOF'
import json, os, sys
R = os.environ["ROUND4_ROOT"]
mtime = int(sys.argv[1]) if sys.argv[1].strip().isdigit() else 0
fed = int(sys.argv[2]) if sys.argv[2].strip().isdigit() else 0
out = {"log_mtime": mtime, "fed_at": fed, "landed": bool(mtime >= fed > 0)}
json.dump(out, open(R + "/rounds/r5_feed.json", "w"), indent=1)
print(out)
PYEOF
