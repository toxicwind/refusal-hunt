import json, os, sys, datetime, subprocess

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
os.makedirs(AUDIT, exist_ok=True)
HITS = os.path.join(AUDIT, "hits.jsonl")
FIXES = os.path.join(AUDIT, "fixes.jsonl")
LATEST = os.path.join(AUDIT, "LATEST.json")
CURSOR = os.path.expanduser("~/hooks/state/sorry-watchdog/cursor")
SWEEPS = os.path.expanduser("~/hooks/state/sorry-watchdog/sweeps.jsonl")

DIGEST_KIND = {
    "b4aefd29108f232f9c0d5a4b030215c1": "primary",
    "582bcbd080daeb3f826c45ed4a83b265": "secondary",
}

def qdb(sql):
    # use hatch-muse-db via python? Use the muse.db tool instead — placeholder; we run via node below
    raise RuntimeError("unused")

def load_refs(path):
    refs = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                    refs.add((o.get("surface"), o.get("ref")))
                except Exception:
                    pass
    return refs

def load_fix_refs(path):
    refs = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                    refs.add((o.get("surface"), o.get("ref")))
                except Exception:
                    pass
    return refs

def iso_utc(epoch):
    return datetime.datetime.fromtimestamp(epoch, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

hits_in = json.load(sys.stdin)  # {"chat": [...], "spawn": [...], "daemon": [...], "sweep_ts": ..., "window_start": ..., "round": ..., "fix_rounds_done": ...}
refs = load_refs(HITS)
fix_refs = load_fix_refs(FIXES)

new_hits = []
for surf in ("chat", "spawn", "daemon"):
    for h in hits_in.get(surf, []):
        key = (surf, h["ref"])
        if key in refs:
            continue
        refs.add(key)
        new_hits.append(h)

with open(HITS, "a") as f:
    for h in new_hits:
        f.write(json.dumps(h, separators=(",", ":")) + "\n")

# fix loop entries: spawn -> redispatched_clean (or unrecoverable if flagged), chat -> observed, daemon -> observed
fixes_added = 0
redispatched = 0
unrecoverable = 0
with open(FIXES, "a") as f:
    for h in new_hits:
        surf = h["surface"]
        key = (surf, h["ref"])
        if key in fix_refs:
            continue
        fix_refs.add(key)
        if surf == "spawn":
            action = "unrecoverable" if h.get("unrecoverable") else "redispatched_clean"
            detail = h.get("fix_detail", "task re-dispatched via clean workflow route")
            if action == "redispatched_clean":
                redispatched += 1
            else:
                unrecoverable += 1
        else:
            action = "observed"
            detail = "turn reached user; logged only"
        f.write(json.dumps({"ts": iso_utc(hits_in["sweep_ts"]), "ref": h["ref"], "surface": surf,
                            "action": action, "detail": detail}, separators=(",", ":")) + "\n")
        fixes_added += 1

print(json.dumps({"persisted": len(new_hits), "fixes_added": fixes_added,
                  "redispatched": redispatched, "unrecoverable": unrecoverable}))
