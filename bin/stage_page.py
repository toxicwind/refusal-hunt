#!/usr/bin/env python3
"""Stage a saved db tool-output page into inbox staging; print its keyset floor."""
import json, os, sys
from collections import Counter

TOOLOUT = os.path.expanduser("~/workspace/agents/7240686c-d790-463d-bad2-c969fc65885e/tool-output")
INBOX = os.path.expanduser("~/workspace/refusal-hunt/ledger/inbox")
os.makedirs(INBOX, exist_ok=True)

def stage(fname, out_name):
    with open(os.path.join(TOOLOUT, fname)) as fh:
        payload = json.load(fh)
    rows = payload["result"]["rows"]
    out_path = os.path.join(INBOX, out_name)
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
    print(f"{fname}: rows={len(rows)} min={cats[0]} max={cats[-1]}")
    print("  digests=" + json.dumps(dict(Counter(r["body_md5"][:8] for r in rows))))
    print("  staged -> " + out_path)
    return cats[0], len(rows)

if __name__ == "__main__":
    stage(sys.argv[1], sys.argv[2])
