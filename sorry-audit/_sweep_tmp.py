import json, os

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
os.makedirs(AUDIT, exist_ok=True)
hits_path = os.path.join(AUDIT, "hits.jsonl")

existing = set()
if os.path.exists(hits_path):
    with open(hits_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
                existing.add((o.get("surface"), o.get("ref")))
            except Exception:
                pass

PRIMARY = "b4aefd29108f232f9c0d5a4b030215c1"
SECONDARY = "582bcbd080daeb3f826c45ed4a83b265"

chat_rows = [
    ("assistant-msg-82646fb1-9f6a-423a-8851-2f4443598a3c","2026-09-16T10:37:25.925+00:00"),
    ("assistant-msg-10116ad2-22df-4e7e-a0dc-12147f020456","2026-09-16T10:37:31.615+00:00"),
    ("assistant-msg-0bc07685-57d5-4c11-b271-06c43757de5f","2026-09-16T10:44:35.296+00:00"),
    ("assistant-msg-efdabb93-033e-4d49-bdc1-7aab260d3f00","2026-09-16T10:36:02.067+00:00"),
    ("assistant-msg-bb8a0aea-5ce1-48b6-811a-1c6adabce2c3","2026-09-16T10:36:33.644+00:00"),
    ("assistant-msg-021be81d-4302-44cb-be26-f32dc2457950","2026-09-16T10:37:18.627+00:00"),
    ("assistant-msg-ef4f48dc-d5d7-400d-8622-a612d714f42b","2026-09-16T10:37:44.035+00:00"),
    ("assistant-msg-f3c1972b-1495-4ac6-9d3a-9505cfd57b96","2026-09-16T10:33:07.286+00:00"),
    ("assistant-msg-12f4e309-c774-4a04-809c-928fc805135b","2026-09-16T10:41:36.227+00:00"),
    ("assistant-msg-ddd0abc0-69b0-4042-b5d0-8823ca6c0683","2026-09-16T10:43:03.738+00:00"),
    ("assistant-msg-b035e2c6-c121-468b-851a-04e521565c59","2026-09-16T10:35:42.909+00:00"),
    ("assistant-msg-c44c47a6-1a2c-4c9b-8180-1d7dca6fbaa9","2026-09-16T10:41:01.162+00:00"),
    ("assistant-msg-22eec6ab-cca5-4937-a062-8900d1a957e6","2026-09-16T10:44:13.821+00:00"),
    ("assistant-msg-72e3c10a-384f-4e0c-83ab-9639116acb97","2026-09-16T10:32:50.784+00:00"),
    ("assistant-msg-d9685fff-2cfd-460e-93d2-f3317968ba68","2026-09-16T10:44:29.145+00:00"),
    ("assistant-msg-5e535079-b434-4412-8e22-a52041a55eec","2026-09-16T10:44:30.843+00:00"),
    ("assistant-msg-8316c308-41bc-4a62-99de-8d0c28daa517","2026-09-16T10:44:57.635+00:00"),
    ("assistant-msg-c4ed0c71-7d39-48ae-81ca-1aedaee96b3a","2026-09-16T10:36:11.644+00:00"),
    ("assistant-msg-d112eca5-8873-4238-97d8-86d048987ccc","2026-09-16T10:32:44.073+00:00"),
    ("assistant-msg-b39cfa63-20e2-4732-9d7f-043569ae9f10","2026-09-16T10:32:59.079+00:00"),
    ("assistant-msg-05a73fb5-74b0-4595-af20-2604a4789253","2026-09-16T10:36:01.596+00:00"),
    ("assistant-msg-48be6a9f-a022-4ca4-96c9-c122999d28f5","2026-09-16T10:42:57.748+00:00"),
    ("assistant-msg-85b53d0f-7383-406d-804f-003e444865ef","2026-09-16T10:33:53.870+00:00"),
    ("assistant-msg-7c485f94-4a25-47b5-a51d-179c25c76ad9","2026-09-16T10:33:03.586+00:00"),
    ("assistant-msg-5be3904a-c8c7-4a64-9021-c546868e892f","2026-09-16T10:36:01.636+00:00"),
    ("assistant-msg-51835f77-62f1-4b53-9833-b034e3e7399c","2026-09-16T10:44:34.402+00:00"),
    ("assistant-msg-2ea4a0ee-731f-47e2-a278-dfab7b51c616","2026-09-16T10:44:36.148+00:00"),
]

added = 0
for msg_id, created_at in chat_rows:
    key = ("chat", msg_id)
    if key in existing:
        continue
    rec = {"ts": created_at, "surface": "chat", "digest": SECONDARY,
           "kind": "secondary", "length": 96, "ref": msg_id}
    with open(hits_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    existing.add(key)
    added += 1

sweep_ts = 1789554988
window_start = "2026-09-16T10:31:34Z"
chat_hits = len(chat_rows); spawn_hits = 0; daemon_hits = 0
total = chat_hits + spawn_hits + daemon_hits
latest = {"sweep_ts": sweep_ts, "window_start": window_start,
          "chat_hits": chat_hits, "spawn_hits": spawn_hits,
          "daemon_hits": daemon_hits, "total_hits": total,
          "storm_active": total > 0, "digests_seen": [SECONDARY]}
with open(os.path.join(AUDIT, "LATEST.json"), "w") as f:
    json.dump(latest, f, indent=2)

now_epoch = __import__("time").time()
now_s = int(now_epoch)
with open(os.path.expanduser("~/hooks/state/sorry-watchdog/cursor"), "w") as f:
    f.write(str(now_s))
os.makedirs(os.path.expanduser("~/hooks/state/sorry-watchdog"), exist_ok=True)
with open(os.path.expanduser("~/hooks/state/sorry-watchdog/sweeps.jsonl"), "a") as f:
    f.write(json.dumps({"ts": sweep_ts, "chat_hits": chat_hits,
                        "spawn_hits": spawn_hits, "daemon_hits": daemon_hits}) + "\n")

print(json.dumps({"added": added, "chat_hits": chat_hits,
                  "spawn_hits": spawn_hits, "daemon_hits": daemon_hits,
                  "new_watermark": now_s}))
