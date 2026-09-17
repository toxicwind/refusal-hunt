#!/usr/bin/env python3
"""echo_collapse.py -- production echo-collapse for the client replay bug.

The client replays refused/failed turns as brand-new user messages, so one
legitimate request becomes dozens of identical rows. Rule (Chris, 2026-09-16):
treat repeated identical bodies as ONE legitimate request plus echo duplicates.

Usage:
  echo_collapse.py < messages.jsonl > collapsed.jsonl
Input rows: {"message_id":..., "role":"user"|"assistant"|"system",
             "body": "...", "created_at": "iso"}
Output rows: one per canonical request:
  {"body_md5":..., "role":..., "canonical_message_id":..., "first_seen":...,
   "last_seen":..., "echo_count":..., "echo_message_ids":[...],
   "is_known_storm_signature": bool}
Assistant rows matching known canned-refusal digests are flagged but kept;
nothing is deleted (additive, forward-only).
"""
import hashlib
import json
import sys

# Digest-only storm signatures. Never store the bodies (loop-fuel rule).
KNOWN_STORM_MD5 = {
    "b4aefd29108f232f9c0d5a4b030215c1",  # 384-char spawn-level canned refusal
    "582bcbd080daeb3f826c45ed4a83b265",  # 96-char chat-level canned refusal
}


def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8", "replace")).hexdigest()


def collapse(rows):
    groups = {}
    order = []
    for r in rows:
        body = r.get("body") or ""
        key = (r.get("role"), md5_hex(body))
        g = groups.get(key)
        if g is None:
            g = {
                "body_md5": key[1],
                "role": r.get("role"),
                "canonical_message_id": r.get("message_id"),
                "first_seen": r.get("created_at"),
                "last_seen": r.get("created_at"),
                "echo_count": 0,
                "echo_message_ids": [],
                "is_known_storm_signature": key[1] in KNOWN_STORM_MD5,
                "body_len": len(body),
            }
            groups[key] = g
            order.append(key)
        else:
            # keep the earliest row as canonical
            if (r.get("created_at") or "") < (g["first_seen"] or ""):
                g["echo_message_ids"].append(g["canonical_message_id"])
                g["canonical_message_id"] = r.get("message_id")
                g["first_seen"] = r.get("created_at")
            else:
                g["echo_message_ids"].append(r.get("message_id"))
                g["last_seen"] = r.get("created_at")
            g["echo_count"] += 1
    return [groups[k] for k in order]


def main() -> int:
    rows = [json.loads(l) for l in sys.stdin if l.strip()]
    for g in collapse(rows):
        sys.stdout.write(json.dumps(g) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
