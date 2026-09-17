#!/usr/bin/env python3
"""Stage chat page 5 (13 rows, inline result) into inbox staging."""
import json, os, uuid

INBOX = os.path.expanduser("~/workspace/refusal-hunt/ledger/inbox")
os.makedirs(INBOX, exist_ok=True)
SEC = "582bcbd080daeb3f826c45ed4a83b265"
P5 = [
 ("assistant-msg-50cf0be1-d94d-4486-a5fe-f7d8dd516267", "2026-09-16 02:58:47.328+00"),
 ("assistant-msg-38a3cdf2-41b3-4b46-a043-7709cf9f07b3", "2026-09-16 02:58:44.473+00"),
 ("assistant-msg-7b6309f1-5a6b-458c-af54-c2e6a0c80b3a", "2026-09-16 02:58:35.25+00"),
 ("assistant-msg-ef2309b9-85fe-4bcb-8334-00716a56b2fd", "2026-09-16 02:57:17.299+00"),
 ("assistant-msg-bc873740-8682-4788-9c55-e1a095981ef8", "2026-09-16 02:57:15.222+00"),
 ("assistant-msg-efd8675b-4b69-434a-b2b4-be83fc501def", "2026-09-16 02:57:08.804+00"),
 ("assistant-msg-78951fae-3b7f-4dd8-a6e6-58479fcb8f53", "2026-09-15 19:59:57.355+00"),
 ("assistant-msg-2aaa686c-1e20-4d13-8a07-b5220a93d59e", "2026-09-15 19:59:51.207+00"),
 ("assistant-msg-90cbfe69-a8f3-4395-a2e9-e3f30a54fec0", "2026-09-15 19:54:14.994+00"),
 ("assistant-msg-2209bd4f-1057-48cd-81f4-ea3696bf36f5", "2026-09-15 19:53:29.233+00"),
 ("assistant-msg-0cbf705c-7aca-46b9-aba4-1ab2e4057131", "2026-09-15 19:36:37.69+00"),
 ("assistant-msg-31134098-068d-4b87-93e4-c95afa699ec0", "2026-09-15 11:04:20.57+00"),
 ("assistant-msg-de59eb02-a734-433b-ad7c-e3fdb7f3644b", "2026-09-15 10:46:04.321+00"),
]
out_path = os.path.join(INBOX, "stage-chat-p5.jsonl")
with open(out_path, "w") as out:
    for mid, ts in P5:
        uuid.UUID(mid.replace("assistant-msg-", ""))
        out.write(json.dumps({
            "source": "chat", "id": mid, "created_at": ts,
            "body_md5": SEC, "body_len": 96, "status": None,
            "parent_agent_id": None, "child_agent_id": None,
        }) + "\n")
print(f"chat p5 rows staged: {len(P5)} -> {out_path}")
