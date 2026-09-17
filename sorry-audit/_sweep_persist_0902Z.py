import json, os, datetime

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
HITS = os.path.join(AUDIT, "hits.jsonl")
FIXES = os.path.join(AUDIT, "fixes.jsonl")

# Round-1 hits from the DB query (window > watermark 1789635695 = 2026-09-17T09:01:35Z)
hits = [
    {"msg": "assistant-msg-77ee4987-5d94-419a-a118-40dd62c402f7", "at": "2026-09-17T09:01:45.619+00:00", "user_digest": "e00ce193650fa939d42dabf6d0e1f7fb"},
    {"msg": "assistant-msg-3db4c1f5-e4c1-4c39-9a87-4fb1fcfe75da", "at": "2026-09-17T09:02:19.229+00:00", "user_digest": "2f95caa0ef0d88365906d31f0b757dfd"},
    {"msg": "assistant-msg-8a8c31c2-11e6-4910-b5a9-f69e2f5158ef", "at": "2026-09-17T09:02:26.841+00:00", "user_digest": "6c818bc94566967cf4bc11e9b47abfb9"},
    {"msg": "assistant-msg-91927874-e368-4477-ac70-b9a9f1761564", "at": "2026-09-17T09:02:32.013+00:00", "user_digest": "6c818bc94566967cf4bc11e9b47abfb9"},
    {"msg": "assistant-msg-86633809-2dca-43e9-bbc4-77442dd050be", "at": "2026-09-17T09:02:35.193+00:00", "user_digest": "6c818bc94566967cf4bc11e9b47abfb9"},
]
SECONDARY = "582bcbd080daeb3f826c45ed4a83b265"
ANSWER_MSG = "assistant-msg-55c8fb13-e0bc-aadd-a2fd-cf182880b291"  # real answer at 09:03:42Z, len 414
now = datetime.datetime.now(datetime.timezone.utc).isoformat()

existing = set()
if os.path.exists(HITS):
    with open(HITS) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
                existing.add((o.get("surface"), o.get("ref")))
            except Exception:
                pass

fixed_existing = set()
if os.path.exists(FIXES):
    with open(FIXES) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
                if o.get("action") in ("reissued", "already_answered"):
                    fixed_existing.add(o.get("ref"))
            except Exception:
                pass

added_hits, added_fixes = 0, 0
with open(HITS, "a") as fh:
    for h in hits:
        if ("chat", h["msg"]) in existing:
            continue
        fh.write(json.dumps({
            "ts": h["at"], "surface": "chat", "digest": SECONDARY,
            "kind": "secondary", "length": 96, "ref": h["msg"]}) + "\n")
        existing.add(("chat", h["msg"]))
        added_hits += 1

with open(FIXES, "a") as ff:
    for h in hits:
        if h["msg"] in fixed_existing:
            continue
        ff.write(json.dumps({
            "ts": now, "ref": h["msg"], "surface": "chat",
            "action": "already_answered",
            "detail": ("nearest preceding user msg digest %s (morphe 1.1.1.1 re-send variant); "
                       "genuine answer delivered AFTER hit at 2026-09-17T09:03:42Z by %s "
                       "(len 414, non-canned; storm-eaten replies explained, 1.1.1.1 canary confirmed); "
                       "two len-0 assistant rows 09:02:48/09:02:51Z are streaming placeholders, not answers")
                       % (h["user_digest"], ANSWER_MSG)}) + "\n")
        fixed_existing.add(h["msg"])
        added_fixes += 1

print(json.dumps({"added_hits": added_hits, "added_fixes": added_fixes, "round": 1}))
