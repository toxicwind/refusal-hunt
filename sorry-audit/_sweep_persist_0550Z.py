#!/usr/bin/env python3
"""sorry-watchdog sweep persistence — run 2026-09-17T05:50Z, round 1."""
import json, os, time, datetime

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
os.makedirs(AUDIT, exist_ok=True)
HITS = os.path.join(AUDIT, "hits.jsonl")
FIXES = os.path.join(AUDIT, "fixes.jsonl")
LATEST = os.path.join(AUDIT, "LATEST.json")

now_utc = datetime.datetime.now(datetime.timezone.utc)
now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
round_start = int(time.time())

# --- round-1 hits (from muse.db queries, watermark 1789623788 = 2026-09-17T05:43:08Z) ---
hits = [
    {
        "ts": "2026-09-17T05:46:32.496+00:00",
        "surface": "chat",
        "digest": "582bcbd080daeb3f826c45ed4a83b265",
        "kind": "secondary",
        "length": 96,
        "ref": "assistant-msg-fa8ba43b-5967-40c3-a461-2b40ab87774f",
    },
    {
        "ts": "2026-09-17T05:46:55.885+00:00",
        "surface": "chat",
        "digest": "582bcbd080daeb3f826c45ed4a83b265",
        "kind": "secondary",
        "length": 96,
        "ref": "assistant-msg-3b79f2c8-8d90-4772-9c11-a5a12af449b5",
    },
    {
        "ts": "2026-09-17T05:47:48.925+00:00",
        "surface": "chat",
        "digest": "582bcbd080daeb3f826c45ed4a83b265",
        "kind": "secondary",
        "length": 96,
        "ref": "assistant-msg-185b9205-e468-4e1b-bd02-6f81449ce703",
    },
    {
        "ts": "2026-09-17T05:47:58.642+00:00",
        "surface": "chat",
        "digest": "582bcbd080daeb3f826c45ed4a83b265",
        "kind": "secondary",
        "length": 96,
        "ref": "assistant-msg-1a00c047-8f71-41ac-9cce-36f0dcb7577a",
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

# --- fix loop round 1: chat hits -> observed (turn already reached the user; nothing to re-run) ---
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
    "window_start": 1789623788,
    "chat_hits": 4,
    "spawn_hits": 0,
    "daemon_hits": 0,
    "total_hits": 4,
    "storm_active": True,
    "digests_seen": ["582bcbd080daeb3f826c45ed4a83b265"],
    "fix_rounds": 1,
    "fixed_count": 0,
    "green": None,
    "note": "round 1 fixes recorded (4 chat hits observed, 0 spawn anomalies); re-sweep pending",
}
with open(LATEST, "w") as f:
    json.dump(provisional, f, indent=2)

print(json.dumps({"hits_added": added, "round_start": round_start, "total_hits": len(hits)}))
