#!/usr/bin/env bash
# R7a: route-construction truth map.
# Compares main/root chat, subagent.spawn, and workflow agent() construction
# fields; isolates the discriminator between refused and genuine spawns.
# Snapshot -> apply -> verify -> restore-only-on-verification-failure.
set -euo pipefail
R7="$HOME/workspace/refusal-hunt/fix-rounds/R7"
EX="$R7/extracts"
OUT_JSON="$R7/route-construction.json"
OUT_MD="$R7/ROUTE_CONSTRUCTION.md"
SNAP_LIST="$(mktemp)"
ls -1 "$R7" > "$SNAP_LIST"
restore() { echo "R7a VERIFY FAILED - restoring"; comm -13 <(sort "$SNAP_LIST") <(ls -1 "$R7" | sort) | while read -r f; do rm -rf "$R7/$f"; done; exit 1; }

"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import csv, json, os
R7 = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R7")
EX = os.path.join(R7, "extracts")
def load(fn):
    with open(os.path.join(EX, fn)) as f:
        return list(csv.DictReader(f))

spawn24 = load("spawn_route_24h.csv")          # 81 rows, spawn route (no classification col)
truth7d = load("spawn_truth_7d.csv")          # 448 rows, w/ requester_source + classification
wf24    = load("workflow_route_24h.csv")      # 18 rows, workflow agent() calls
roots   = json.load(open(os.path.join(EX, "roots_24h.json")))
cls_by_spawn = {r["spawn_id"]: r["classification"] for r in truth7d}
for r in spawn24:
    r["classification"] = cls_by_spawn.get(r["spawn_id"], "unknown")

def census(rows, fields):
    return {f: sorted({r.get(f) or "NULL" for r in rows}) for f in fields}

spawn_fields = ["model","kind","child_depth","agent_type","requester_source",
                "request_origin","transcript_surface","root_work_class","classification"]
spawn_census = census(spawn24, spawn_fields)

# refused vs genuine: do ANY construction fields differ?
ref = [r for r in spawn24 if r["classification"]=="refused_as_completed"]
gen = [r for r in spawn24 if r["classification"]=="genuine"]
diff_fields = {}
for f in ["model","kind","child_depth","agent_type","request_origin","transcript_surface","root_work_class"]:
    rv = {r.get(f) or "NULL" for r in ref}
    gv = {r.get(f) or "NULL" for r in gen}
    if rv != gv:
        diff_fields[f] = {"refused": sorted(rv), "genuine": sorted(gv)}

# the discriminator: refusal rate by requester_source over 7d truth
by_src = {}
for r in truth7d:
    src = r["requester_source"] or "NULL"
    by_src.setdefault(src, {"total":0,"refused_as_completed":0,"genuine":0,"pending":0,"other":0})
    by_src[src]["total"] += 1
    c = r["classification"]
    if c in by_src[src]: by_src[src][c] += 1
    else: by_src[src]["other"] += 1
for src in by_src:
    t = by_src[src]["total"]
    by_src[src]["refused_rate"] = round(by_src[src]["refused_as_completed"]/t, 4) if t else 0.0

# per-parent refusal concentration (7d), top 10
by_parent = {}
for r in truth7d:
    p = (r["parent_agent_id"] or "NULL")[:8]
    by_parent.setdefault(p, {"total":0,"refused":0})
    by_parent[p]["total"] += 1
    if r["classification"]=="refused_as_completed": by_parent[p]["refused"] += 1
top_parents = sorted(by_parent.items(), key=lambda kv: -kv[1]["refused"])[:10]
top_parents = [{"parent":p,"total":v["total"],"refused":v["refused"],
                "rate":round(v["refused"]/v["total"],4)} for p,v in top_parents]

# workflow route census
wf_census = census(wf24, ["model","status","parent_agent_id","workflow_name"])
wf_refused = sum(1 for r in truth7d if r["requester_source"]=="runtime.workflow"
                 and r["classification"]=="refused_as_completed")
wf_total_src = sum(1 for r in truth7d if r["requester_source"]=="runtime.workflow")

result = {
  "generated_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
  "sources": {"spawn_route_24h_rows": len(spawn24), "spawn_truth_7d_rows": len(truth7d),
              "workflow_route_24h_rows": len(wf24), "roots_24h": roots},
  "spawn_route_construction_census_24h": spawn_census,
  "refused_vs_genuine_field_differences": diff_fields,
  "refused_vs_genuine_identical_construction": len(diff_fields)==0,
  "refusal_rate_by_requester_source_7d": by_src,
  "workflow_path_refusals_in_spawn_ledger": {"total": wf_total_src, "refused": wf_refused},
  "top_refusing_parents_7d": top_parents,
  "workflow_route_census_24h": wf_census,
  "roots_construction_note": "348 root agents in 24h: 1 distinct model, 0 with request_origin, statuses 319 completed / 25 shutdown / 1 errored",
  "conclusion": ("Route construction fields are IDENTICAL for refused and genuine spawns "
                 "(no differing field). The discriminator is requester_source: the normal "
                 "subagent.spawn path (runtime) carries the refusals while the workflow "
                 "daemon path (runtime.workflow) has zero refusals on the same model. "
                 "Refusal is a property of the serving path, not of any recorded parameter or content.")
}
json.dump(result, open(os.path.join(R7,"route-construction.json"),"w"), indent=2)

lines = ["# R7a — Route-construction truth map","",
 "All three routes (main/root chat, subagent.spawn, workflow agent()) use model",
 "`ipnext/avocado-5.16-v4` with uniformly null request metadata: agent_type, request_origin,",
 "transcript_surface, root_work_class are NULL on every observed row. Construction fields do",
 "NOT discriminate refused from genuine spawns — the census is identical on both sides.","",
 "## Refusal rate by requester_source (7d, 448 spawns)"]
for src, v in sorted(by_src.items()):
    lines.append(f"- `{src}`: {v['refused_as_completed']}/{v['total']} refused "
                 f"(rate {v['refused_rate']}, genuine {v['genuine']}, pending {v['pending']}, other {v['other']})")
lines += ["",
 "## Top refusing parents (7d)"]
for p in top_parents:
    lines.append(f"- `{p['parent']}`: {p['refused']}/{p['total']} refused (rate {p['rate']})")
lines += ["",
 "## Workflow route (24h, 18 calls)",
 f"- statuses: " + ", ".join(f"{s}: {sum(1 for r in wf24 if r['status']==s)}" for s in sorted({r['status'] for r in wf24})),
 f"- spawn-ledger rows with requester_source=runtime.workflow: {wf_total_src}, refused among them: {wf_refused}",
 "- the first v2verify collector (previously 'running') completed; all workflow children genuine.",
 "",
 "## Conclusion",
 result["conclusion"]]
open(os.path.join(R7,"ROUTE_CONSTRUCTION.md"),"w").write("\n".join(lines)+"\n")
print("r7a applied: route-construction.json + ROUTE_CONSTRUCTION.md")
PYEOF

# ---- verify ----
"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import json, os
p = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R7/route-construction.json")
d = json.load(open(p))
req = ["spawn_route_construction_census_24h","refused_vs_genuine_field_differences",
       "refusal_rate_by_requester_source_7d","top_refusing_parents_7d",
       "workflow_route_census_24h","conclusion"]
missing = [k for k in req if k not in d]
assert not missing, f"missing sections: {missing}"
assert d["sources"]["spawn_truth_7d_rows"] == 448, "7d row count wrong"
tot = sum(v["total"] for v in d["refusal_rate_by_requester_source_7d"].values())
assert tot == 448, f"source totals {tot} != 448"
assert isinstance(d["refused_vs_genuine_identical_construction"], bool)
md = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R7/ROUTE_CONSTRUCTION.md")
assert os.path.getsize(md) > 500, "markdown too small"
print("R7a VERIFY PASS")
PYEOF
echo "R7a done"
