#!/usr/bin/env python3
"""Checkpoint-distance measurement for the true main session (agent 0693e1c3).
Quarantine: digests and counts only, no bodies printed."""
import json, hashlib, bisect

p = "/home/hatch/agents/agent-0693e1c3-6054-49ab-a712-95a94748017e/sessions/0693e1c3-6054-49ab-a712-95a94748017e.jsonl"
S96 = "582bcbd080daeb3f826c45ed4a83b265"
S384 = "b4aefd29108f232f9c0d5a4b030215c1"

lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
ckpt = []
hits96 = []
hits384 = []
for i, line in enumerate(lines, 1):
    s = line.strip()
    if '"checkpoint"' in s or 'compaction' in s[:300].lower():
        ckpt.append(i)
    try:
        obj = json.loads(s)
    except Exception:
        continue

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("text", "content", "body") and isinstance(v, str) and v:
                    yield v
                else:
                    yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)

    seen96 = seen384 = False
    for cand in walk(obj):
        d = hashlib.md5(cand.encode()).hexdigest()
        if d == S96:
            seen96 = True
        elif d == S384:
            seen384 = True
    if seen96:
        hits96.append(i)
    if seen384:
        hits384.append(i)

def dists_to(hits):
    out = []
    for h in hits:
        j = bisect.bisect_left(ckpt, h)
        cand = []
        if j < len(ckpt):
            cand.append(abs(h - ckpt[j]))
        if j > 0:
            cand.append(abs(h - ckpt[j - 1]))
        out.append(min(cand) if cand else None)
    return out

def summarize(dists):
    sd = sorted(d for d in dists if d is not None)
    buckets = {"0-5": 0, "6-20": 0, "21-50": 0, "51+": 0}
    for d in sd:
        buckets["0-5" if d <= 5 else "6-20" if d <= 20 else "21-50" if d <= 50 else "51+"] += 1
    return {"n": len(sd), "buckets": buckets,
            "median": sd[len(sd) // 2] if sd else None,
            "max": max(sd) if sd else None}

print(json.dumps({
    "lines": len(lines),
    "checkpoints": len(ckpt),
    "hits96": summarize(dists_to(hits96)),
    "hits384": summarize(dists_to(hits384)),
    "first96_line": hits96[0] if hits96 else None,
    "last96_line": hits96[-1] if hits96 else None,
}))
