import json, os, datetime

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")

hits = [
    ("assistant-msg-0d84202d-e429-45ea-830a-052a5a434a28", "2026-09-17T06:52:33.072+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-9c12b171-1632-4e19-86ac-61622d4c3ed7", "2026-09-17T06:52:36.858+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-5ffe73c0-fbfa-4c54-b2a9-cb558b12460a", "2026-09-17T06:52:40.573+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-2b91c0ae-7b2c-41e4-b483-16920439804e", "2026-09-17T06:52:43.389+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-f9cdc625-e9a8-4c85-884c-a4068dda725a", "2026-09-17T06:52:51.749+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-5b359072-4c06-427f-b735-6f8374c5856e", "2026-09-17T06:52:56.145+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-59c18caa-6a98-4cec-a17c-e952e5d70d26", "2026-09-17T06:52:56.876+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
    ("assistant-msg-7a62a197-5022-4854-af81-02d3cdd5ab2f", "2026-09-17T06:52:58.473+00:00", "582bcbd080daeb3f826c45ed4a83b265", 96),
]

KIND = {"582bcbd080daeb3f826c45ed4a83b265": "secondary",
        "b4aefd29108f232f9c0d5a4b030215c1": "primary"}

# dedupe: existing (surface, ref) pairs
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
fp = os.path.join(AUDIT, "fixes.jsonl")
with open(fp, "a") as f:
    for msg_id, ts, digest, ln in hits:
        f.write(json.dumps({"ts": now, "ref": msg_id, "surface": "chat",
                            "action": "observed",
                            "detail": "chat-surface hit: turn already reached user; logged for audit, nothing to re-run"}) + "\n")

print(json.dumps({"persisted_new": new_hits, "fix_lines_written": len(hits)}))
