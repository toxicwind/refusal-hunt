#!/usr/bin/env python3
"""sorry-watchdog sweep persistence — run 2026-09-17T03:38Z, round 1."""
import json, os, time, datetime

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
os.makedirs(AUDIT, exist_ok=True)
HITS = os.path.join(AUDIT, "hits.jsonl")
FIXES = os.path.join(AUDIT, "fixes.jsonl")
LATEST = os.path.join(AUDIT, "LATEST.json")

now_utc = datetime.datetime.now(datetime.timezone.utc)
now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
round_start = int(time.time())

KIND = {
    "b4aefd29108f232f9c0d5a4b030215c1": "primary",
    "582bcbd080daeb3f826c45ed4a83b265": "secondary",
}

# --- round-1 hits (from muse.db queries, watermark 1789616046) ---
hits = [
    {
        "ts": "2026-09-17T03:36:55.024Z",
        "surface": "chat",
        "digest": "582bcbd080daeb3f826c45ed4a83b265",
        "kind": "secondary",
        "length": 96,
        "ref": "assistant-msg-f2c5a3e2-3019-41c3-a09f-3c7e9f7a0f7b",
    },
]

# --- append hits with dedup on (surface, ref) ---
existing = set()
if os.path.exists(HITS):
    with open(HITS) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                h = json.loads(line)
                existing.add((h.get("surface"), h.get("ref")))
            except Exception:
                continue

added = 0
for h in hits:
    if (h["surface"], h["ref"]) not in existing:
        with open(HITS, "a") as f:
            f.write(json.dumps(h) + "\n")
        existing.add((h["surface"], h["ref"]))
        added += 1

# --- fix loop round 1: chat hit -> observed (nothing to re-run) ---
for h in hits:
    fix = {
        "ts": now_iso,
        "ref": h["ref"],
        "surface": h["surface"],
        "action": "observed",
        "detail": "chat-surface canned-refusal turn reached the user; no re-run applies; recorded in ledger",
    }
    with open(FIXES, "a") as f:
        f.write(json.dumps(fix) + "\n")

# --- provisional LATEST.json (re-sweep pending; will be finalized after) ---
provisional = {
    "sweep_ts": now_utc.timestamp(),
    "window_start": 1789616046,
    "chat_hits": 1,
    "spawn_hits": 0,
    "daemon_hits": 0,
    "total_hits": 1,
    "storm_active": True,
    "digests_seen": ["582bcbd080daeb3f826c45ed4a83b265"],
    "fix_rounds": 1,
    "fixed_count": 0,
    "green": None,
    "note": "round 1 fixes recorded (chat observed); re-sweep pending",
}
with open(LATEST, "w") as f:
    json.dump(provisional, f, indent=2)

print(json.dumps({"hits_added": added, "round_start": round_start, "total_hits": len(hits)}))
