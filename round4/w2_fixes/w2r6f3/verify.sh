#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os, subprocess
R = os.environ["ROUND4_ROOT"]
fed = int(open(R + "/input/w2_feed_ts.txt").read().strip())
out = subprocess.run(["python3", os.path.expanduser("~/workspace/skills/awrawr-mcp/bin/exec.py"),
                      "--timeout", "15", "stat -c %Y /home/toxic/refusal-hunt/canary/log.jsonl"],
                     capture_output=True, text=True, timeout=60)
mtime = int(out.stdout.strip().splitlines()[-1])
landed = mtime >= fed > 0
json.dump({"log_mtime": mtime, "fed_at": fed, "landed": landed},
          open(R + "/rounds/w2_feed.json", "w"), indent=1)
assert landed, (mtime, fed)
print("FEED_REPROBE_OK", mtime, fed)
PYEOF
