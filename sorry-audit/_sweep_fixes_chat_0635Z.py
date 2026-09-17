#!/usr/bin/env python3
"""Record chat-surface hits as observed (round 1, sweep 1789625730)."""
import json, os, datetime

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
FIXES = os.path.join(AUDIT, "fixes.jsonl")
ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
WINDOW_START = "2026-09-17T06:09:35"  # watermark 1789625375 = 06:09:35 UTC (00:09:35 MDT)
dec = json.JSONDecoder()
# avoid duplicates: refs already recorded in fixes.jsonl
done = set()
if os.path.exists(FIXES):
    with open(FIXES) as fx:
        for line in fx:
            line = line.strip()
            if not line:
                continue
            idx = 0
            while idx < len(line):
                while idx < len(line) and line[idx] not in "{[":
                    idx += 1
                if idx >= len(line):
                    break
                try:
                    d, end = dec.raw_decode(line, idx)
                except Exception:
                    break
                idx = end
                done.add((d.get("surface"), str(d.get("ref"))))
n = 0
with open(FIXES, "a") as f:
    with open(os.path.join(AUDIT, "hits.jsonl")) as h:
        for line in h:
            line = line.strip()
            if not line:
                continue
            # tolerate multiple JSON objects concatenated on one physical line
            idx = 0
            while idx < len(line):
                while idx < len(line) and line[idx] not in "{[":
                    idx += 1
                if idx >= len(line):
                    break
                try:
                    d, end = dec.raw_decode(line, idx)
                except Exception:
                    break
                idx = end
                if (d.get("surface") == "chat" and str(d.get("ts", "")) >= WINDOW_START
                        and ("chat", str(d.get("ref"))) not in done):
                    f.write(json.dumps({"ts": ts, "ref": d["ref"], "surface": "chat",
                        "action": "observed",
                        "detail": "chat-surface canned-refusal turn reached the user; no re-run applies (round 1 of sweep 1789625730); digest 582bcbd080daeb3f826c45ed4a83b265 len 96"}) + "\n")
                    n += 1
print(json.dumps({"chat_observed": n}))
