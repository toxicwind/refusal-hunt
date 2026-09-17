#!/usr/bin/env python3
"""sorry-watchdog sweep persistence (round 1, sweep_ts 1789605755)."""
import json, os

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
SECONDARY = "582bcbd080daeb3f826c45ed4a83b265"

HITS = [
    ("assistant-msg-b7943de7-8989-4afd-987c-dcb00d5f8753", "2026-09-17T00:39:59.653+00:00"),
    ("assistant-msg-e3b74baa-db13-4b50-8b63-ec62e7978c8f", "2026-09-17T00:40:02.564+00:00"),
    ("assistant-msg-7a688e33-18a4-44c4-ac4c-444c6c660872", "2026-09-17T00:40:05.067+00:00"),
    ("assistant-msg-2aeb544f-9d86-43c5-b883-14231718f185", "2026-09-17T00:40:07.837+00:00"),
    ("assistant-msg-6835d14f-257c-441e-b0f6-dd6491b63791", "2026-09-17T00:40:12.606+00:00"),
    ("assistant-msg-f5fa8066-d2f0-44a9-b698-ef47146fcfc3", "2026-09-17T00:41:01.391+00:00"),
    ("assistant-msg-e29a395f-3f7b-4256-8f2e-bd858041583c", "2026-09-17T00:41:08.839+00:00"),
    ("assistant-msg-19abb960-8e0c-4ef7-9f83-007ad572a39e", "2026-09-17T00:41:11.954+00:00"),
    ("assistant-msg-0086c651-27c4-4c25-8d05-b32832dafb26", "2026-09-17T00:41:14.154+00:00"),
    ("assistant-msg-65e13012-259c-4717-978d-a909e2f01ed3", "2026-09-17T00:41:16.158+00:00"),
]

def existing_keys(path):
    keys = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                    keys.add((o.get("surface"), o.get("ref")))
                except Exception:
                    continue
    return keys

hits_path = os.path.join(AUDIT, "hits.jsonl")
fixes_path = os.path.join(AUDIT, "fixes.jsonl")
seen = existing_keys(hits_path)
new_hits = 0
new_fixes = 0
fix_seen = existing_keys(fixes_path)

with open(hits_path, "a") as hf, open(fixes_path, "a") as ff:
    for mid, ts in HITS:
        key = ("chat", mid)
        if key not in seen:
            hf.write(json.dumps({
                "ts": ts, "surface": "chat", "digest": SECONDARY,
                "kind": "secondary", "length": 96, "ref": mid,
            }) + "\n")
            seen.add(key)
            new_hits += 1
        if key not in fix_seen:
            ff.write(json.dumps({
                "ts": "2026-09-17T00:43:00Z", "ref": mid, "surface": "chat",
                "action": "observed",
                "detail": "secondary-digest canned assistant row; turn already reached user; nothing to re-run",
            }) + "\n")
            fix_seen.add(key)
            new_fixes += 1

print(json.dumps({"new_hits": new_hits, "new_fixes": new_fixes}))
