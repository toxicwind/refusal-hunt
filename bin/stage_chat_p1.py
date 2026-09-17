#!/usr/bin/env python3
"""Stage chat page-1 rows from the saved db tool output into inbox staging."""
import json, os

SRC = os.path.expanduser("~/workspace/agents/7240686c-d790-463d-bad2-c969fc65885e/tool-output/db-call_01a0a9cdb00e7c00b33e37201ea66928.json")
INBOX = os.path.expanduser("~/workspace/refusal-hunt/ledger/inbox")
os.makedirs(INBOX, exist_ok=True)

with open(SRC) as fh:
    payload = json.load(fh)

rows = payload["result"]["rows"]
print(f"page1 rows={len(rows)}")

out_path = os.path.join(INBOX, "stage-chat-p1.jsonl")
with open(out_path, "w") as out:
    for r in rows:
        out.write(json.dumps({
            "source": r["source"],
            "id": r["id"],
            "created_at": r["created_at"],
            "body_md5": r["body_md5"],
            "body_len": r["body_len"],
            "status": r.get("status"),
            "parent_agent_id": r.get("parent_agent_id"),
            "child_agent_id": r.get("child_agent_id"),
        }) + "\n")

cats = sorted(r["created_at"] for r in rows)
from collections import Counter
print("min_created_at=" + cats[0])
print("max_created_at=" + cats[-1])
print("digests=" + json.dumps(dict(Counter(r["body_md5"] for r in rows))))
print("staged -> " + out_path)
