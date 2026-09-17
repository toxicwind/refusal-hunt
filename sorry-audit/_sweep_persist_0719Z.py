import json, os, datetime

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")

# Round 1 hits, window (1789628830, 1789629520] UTC; all secondary digest, len 96.
hits = [
    ("assistant-msg-65815985-ce41-4ccf-bef9-265aa50cec42", "2026-09-17T07:07:35.057+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-7f54f53b-4374-4a89-b392-59d014357e22", "2026-09-17T07:07:41.012+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-c9580a32-a091-47ea-ac34-6811be618b6a", "2026-09-17T07:07:42.947+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-f63afcad-4332-4d0c-a3c9-cba79a1e1836", "2026-09-17T07:07:48.387+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-0d2591a1-a4c0-4864-a358-e840e9202687", "2026-09-17T07:07:49.991+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-9142037d-7c04-4ca7-9985-22f5f5020bd1", "2026-09-17T07:07:51.974+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-3d54eb32-0e5d-4fac-9ded-2efc6d1faa6d", "2026-09-17T07:07:52.762+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-e420e6d0-550d-4cf3-b9b4-390c9404db59", "2026-09-17T07:07:58.09+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-53fcfa4c-20cd-47cb-9524-ba753f32030b", "2026-09-17T07:08:04.393+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-96132460-0353-4a0c-af22-b14c236557e6", "2026-09-17T07:08:07.929+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-fb61f5a9-509f-43d5-ab4f-ba0805fa9398", "2026-09-17T07:08:09.043+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-b3a8effc-d527-4f44-ba45-b98d4f06ad3a", "2026-09-17T07:08:11.715+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-bfb7edd6-579f-4b0a-a6c6-29b947cd8f6c", "2026-09-17T07:08:13.333+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-ec506247-a061-4167-a0c9-ae7e6a4937bb", "2026-09-17T07:08:17.943+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-bc1384e5-67b9-4040-a786-8161ba47f556", "2026-09-17T07:08:18.9+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-7def7b45-5770-4707-8a3b-403d1673a463", "2026-09-17T07:08:20.037+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-9e4cccc5-e9a5-4ca1-a26f-b540ea301525", "2026-09-17T07:08:22.158+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-904e8874-7d5c-45d7-9908-19f905c339a9", "2026-09-17T07:08:29.505+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-d0ea612d-e17c-44ca-a469-8dc22509f205", "2026-09-17T07:10:54.147+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-08077d8b-df7f-45d1-b0c0-0a1a89bd72c8", "2026-09-17T07:11:08.462+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-7429f6cf-2e24-4064-b17a-88ea0126b1a6", "2026-09-17T07:11:48.611+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-8d525483-0aae-46d8-83dc-26c310430a22", "2026-09-17T07:11:55.709+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-e8e7cb2a-f70c-47ed-be37-183aecd339d0", "2026-09-17T07:11:57.453+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-10dee7a0-08ae-4aee-a9ea-a7a231c087a1", "2026-09-17T07:12:46.025+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-c3cfaa53-1953-4a64-b924-8d5e84493c7c", "2026-09-17T07:16:09.52+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-195bc573-c43c-41d2-9e0a-99e9d56c1eb9", "2026-09-17T07:17:22.761+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-0de10f15-d950-4833-8b4c-a50e7fa06db5", "2026-09-17T07:18:08.137+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-d3cf8ac7-eb6c-44c3-a2aa-3d70ecc6e6b1", "2026-09-17T07:18:21.076+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-6b67a2a3-4234-484f-82b7-ffd0076d54e2", "2026-09-17T07:18:32.506+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
]

KIND = {"582bcbd080daeb3f826c45ed4a83b265": "secondary",
        "b4aefd29108f232f9c0d5a4b030215c1": "primary"}

seen = set()
hp = os.path.join(AUDIT, "hits.jsonl")
if os.path.exists(hp):
    with open(hp) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
                seen.add((o.get("surface"), o.get("ref")))
            except Exception:
                pass

new_hits = 0
with open(hp, "a") as f:
    for msg_id, ts, digest, ln in hits:
        if ("chat", msg_id) in seen:
            continue
        f.write(json.dumps({"ts": ts, "surface": "chat", "digest": digest,
                            "kind": KIND[digest], "length": ln, "ref": msg_id}) + "\n")
        new_hits += 1

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
fix_lines = 0
fp = os.path.join(AUDIT, "fixes.jsonl")
with open(fp, "a") as f:
    for msg_id, ts, digest, ln in hits:
        f.write(json.dumps({"ts": now, "ref": msg_id, "surface": "chat",
                            "action": "observed",
                            "detail": "chat-surface hit: turn already reached user; logged for audit, nothing to re-run"}) + "\n")
        fix_lines += 1

print(json.dumps({"input_hits": len(hits), "persisted_new": new_hits, "fix_lines_written": fix_lines}))
