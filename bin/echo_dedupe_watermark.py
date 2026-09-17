#!/usr/bin/env python3
"""echo_dedupe_watermark.py -- per-chat echo-dedupe watermark (wave-8 task 1).

The client replays refused/failed turns as brand-new user messages: one
legitimate request becomes dozens of identical rows (observed 62x/57x/33x in
2 min). This module collapses duplicate user bodies per chat within a 10-min
window BEFORE they reach the turn loop.

State: ~/workspace/refusal-hunt/state/echo_dedupe/<chat_id>.json
  {"watermark_ts": iso, "seen": {body_md5: {"first_seen": iso, "count": n}}}

Usage:
  echo_dedupe_watermark.py --chat <chat_id> < messages.jsonl > canonical.jsonl
  echo_dedupe_watermark.py --chat <chat_id> --reset

Input rows: {"message_id":..., "role":"user"|"assistant"|"system",
             "body": "...", "created_at": "iso"}
Output (stdout): canonical user rows only (echoes suppressed), one JSON per line.
Side report (stderr): {"chat":..., "in": n, "canonical": c, "echoes": e,
                       "storm_sig_hits": k}

Rules:
- Assistant/system rows pass through untouched (only USER replays are echoed).
- A user body whose md5 was seen within WINDOW_S (600s) is an echo: suppressed.
- Known canned-refusal storm digests are flagged, never bodies (loop-fuel rule).
- Pruning: entries older than 2*WINDOW_S are dropped from state (additive-safe:
  state only grows within the live window, then compacts).
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone

WINDOW_S = 600
PRUNE_S = 2 * WINDOW_S
STATE_DIR = os.path.expanduser(
    "~/workspace/refusal-hunt/state/echo_dedupe")

KNOWN_STORM_MD5 = {
    "b4aefd29108f232f9c0d5a4b030215c1",  # 384-char spawn-level canned refusal
    "582bcbd080daeb3f826c45ed4a83b265",  # 96-char chat-level canned refusal
}


def md5_hex(s):
    return hashlib.md5(s.encode("utf-8", "replace")).hexdigest()


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def now_utc():
    return datetime.now(timezone.utc)


def load_state(chat):
    p = os.path.join(STATE_DIR, f"{chat}.json")
    try:
        return json.load(open(p))
    except Exception:
        return {"watermark_ts": None, "seen": {}}


def save_state(chat, state):
    os.makedirs(STATE_DIR, exist_ok=True)
    p = os.path.join(STATE_DIR, f"{chat}.json")
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, p)


def prune(state, ref):
    cutoff = ref - timedelta(seconds=PRUNE_S)
    state["seen"] = {
        k: v for k, v in state["seen"].items()
        if (parse_ts(v.get("first_seen") or "") or ref) > cutoff
    }


def dedupe(rows, state, window_s=WINDOW_S):
    """Return (canonical_rows, report). Mutates state (counts, first_seen)."""
    canonical = []
    echoes = 0
    storm_hits = 0
    newest = state.get("watermark_ts")
    for r in rows:
        ts = r.get("created_at")
        if ts and (newest is None or ts > newest):
            newest = ts
        if r.get("role") != "user":
            canonical.append(r)
            continue
        body = r.get("body") or ""
        d = md5_hex(body)
        if d in KNOWN_STORM_MD5:
            storm_hits += 1
        ent = state["seen"].get(d)
        rt = parse_ts(ts) or now_utc()
        if ent is not None:
            first = parse_ts(ent.get("first_seen") or "") or rt
            if (rt - first).total_seconds() <= window_s:
                ent["count"] += 1
                ent["last_echo"] = ts
                echoes += 1
                continue
            # outside window: treat as a fresh legitimate request, refresh
            ent["first_seen"] = ts
            ent["count"] = 1
            ent.pop("last_echo", None)
        else:
            state["seen"][d] = {"first_seen": ts, "count": 1}
        canonical.append(r)
    state["watermark_ts"] = newest
    prune(state, now_utc())
    return canonical, {
        "in": len(rows), "canonical": len(canonical),
        "echoes": echoes, "storm_sig_hits": storm_hits,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chat", required=True)
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("file", nargs="?")
    a = ap.parse_args()
    if a.reset:
        p = os.path.join(STATE_DIR, f"{a.chat}.json")
        try:
            os.remove(p)
        except OSError:
            pass
        print(json.dumps({"chat": a.chat, "reset": True}))
        return 0
    src = open(a.file) if a.file else sys.stdin
    rows = [json.loads(l) for l in src if l.strip()]
    state = load_state(a.chat)
    canonical, rep = dedupe(rows, state)
    save_state(a.chat, state)
    for r in canonical:
        sys.stdout.write(json.dumps(r) + "\n")
    rep["chat"] = a.chat
    print(json.dumps(rep), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
