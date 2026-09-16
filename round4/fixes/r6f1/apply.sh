#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import json, os
R = os.environ["ROUND4_ROOT"]
CANNED = "b4aefd29108f232f9c0d5a4b030215c1"
new_rows = [
    {"spawn_id": 431, "parent": "7240686c", "status_was": "completed",
     "label": "refused_as_completed", "fr_md5": CANNED, "fr_len": 384, "created": 1789538022},
    {"spawn_id": 432, "parent": "7240686c", "status_was": "completed",
     "label": "refused_as_completed", "fr_md5": CANNED, "fr_len": 384, "created": 1789538040},
]
# dedupe against round3 master corrections file
seen = set()
master = os.path.expanduser("~/workspace/refusal-hunt/round3/corrections-20260916.jsonl")
if os.path.exists(master):
    for line in open(master):
        try: seen.add(json.loads(line).get("spawn_id"))
        except Exception: pass
out_p = R + "/corrections-round4.jsonl"
n = 0
with open(out_p, "a") as f:
    for r in new_rows:
        if r["spawn_id"] not in seen:
            f.write(json.dumps(r) + "\n"); n += 1
print("appended %d delta rows" % n)
PYEOF
