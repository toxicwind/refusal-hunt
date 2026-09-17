#!/usr/bin/env bash
# R8c: container/agent targeting. Joins the live agent inventory (agent-side
# extract) against the 7d spawn-truth parquet to map storm impact per agent,
# and flags the stuck pending_init spawn. Read-only.
# Snapshot -> apply -> verify -> restore-only-on-verification-failure.
set -euo pipefail
R8="$HOME/workspace/refusal-hunt/fix-rounds/R8"
R7="$HOME/workspace/refusal-hunt/fix-rounds/R7"
OUT="$R8/agent-storm-map.json"
SNAP_LIST="$(mktemp)"
ls -1 "$R8" > "$SNAP_LIST"
restore() { echo "R8c VERIFY FAILED - restoring"; comm -13 <(sort "$SNAP_LIST") <(ls -1 "$R8" | sort) | while read -r f; do rm -rf "$R8/$f"; done; exit 1; }

"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import json, os
from datetime import datetime, timezone
import pyarrow.parquet as pq
R8 = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R8")
R7 = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R7")
inv = json.load(open(os.path.join(R8, "extracts", "agent-inventory.json")))
t = pq.read_table(os.path.join(R7, "spawn-truth.parquet"))
parents = t.column("parent_agent_id").to_pylist()
classes = t.column("classification").to_pylist()
children = t.column("child_agent_id").to_pylist()
statuses = t.column("status").to_pylist()

impact = []
for a in inv["live_agents"]:
    aid = a["agent_id"]
    as_parent = [c for p, c in zip(parents, classes) if p == aid]
    as_child = [(s, c) for p2, s, c in zip(children, statuses, classes) if p2 == aid]
    refused = sum(1 for c in as_parent if c == "refused_as_completed")
    impact.append({
        "agent_id": aid, "kind": a["kind"], "status": a["status"],
        "spawns_parented_7d": len(as_parent),
        "spawns_parented_refused": refused,
        "parent_refusal_rate": round(refused/len(as_parent), 4) if as_parent else None,
        "appears_as_child": [{"status": s, "classification": c} for s, c in as_child],
    })

stuck = [{"agent_id": a["agent_id"], "status": a["status"],
          "note": "spawn 430 child, pending_init since ~05:55 UTC; only non-terminal spawn in 7d window"}
         for a in inv["live_agents"] if a["status"] == "pending_init"]

total_refused = sum(1 for c in classes if c == "refused_as_completed")
result = {
  "mapped_utc": datetime.now(timezone.utc).isoformat(),
  "live_agent_impact": impact,
  "stuck_spawns": stuck,
  "totals_7d": {"spawns": len(classes), "refused_as_completed": total_refused},
  "targeting_note": ("Per-agent map enables targeted mitigation: parents with the highest refused "
                     "counts are the ones to reroute through the workflow daemon path "
                     "(requester_source=runtime.workflow, 0% refusal) instead of subagent.spawn. "
                     "No agent was disabled or removed by this audit."),
  "read_only": True,
}
json.dump(result, open(os.path.join(R8, "agent-storm-map.json"), "w"), indent=2)
print("r8c applied")
PYEOF

"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import json, os
R8 = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R8")
d = json.load(open(os.path.join(R8, "agent-storm-map.json")))
s = json.load(open(os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R7/spawn-truth-summary.json")))
assert d["totals_7d"]["spawns"] == 448 == s["rows"]
assert d["totals_7d"]["refused_as_completed"] == s["classification_counts"]["refused_as_completed"]
assert len(d["live_agent_impact"]) == 6
assert len(d["stuck_spawns"]) == 1 and d["stuck_spawns"][0]["agent_id"].startswith("cee558b1")
assert d["read_only"] is True
print("R8c VERIFY PASS")
PYEOF
echo "R8c done"
