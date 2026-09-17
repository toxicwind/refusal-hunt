#!/usr/bin/env python3
"""live-trace.py — refusal interrupt tracer.

Watches every agent session JSONL under /home/hatch/agents/agent-*/sessions/.
The SECOND a canned refusal digest lands (assistant message or tool output),
it freezes the crime scene: full incident bundle written to
~/workspace/refusal-hunt/live-trace/incidents.jsonl within seconds.

Digest-only: the canned body text is NEVER stored or quoted (quoting re-seeds
the classifier and the client echo loop). md5+length only.

Covers chat turns, subagent spawn results, AND scheduler/cron agent sessions —
they all write session JSONLs.
"""
import glob
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
TRACE_DIR = os.path.join(HOME, "workspace", "refusal-hunt", "live-trace")
INCIDENTS = os.path.join(TRACE_DIR, "incidents.jsonl")
OFFSETS = os.path.join(TRACE_DIR, "offsets.json")
LATEST = os.path.join(TRACE_DIR, "LATEST.json")
LOG = os.path.join(TRACE_DIR, "daemon.log")

# Canned refusal digests (md5 of full body). Benign canary digests excluded.
REFUSAL_DIGESTS = {
    "b4aefd29108f232f9c0d5a4b030215c1",  # storm refusal, 384 chars (spawn path)
    "582bcbd080daeb3f826c45ed4a83b265",  # short assistant variant, 96 chars
}
BENIGN_DIGESTS = {
    "6fdb087aa3fbfbcb8287a593a0919e61",  # canary 'pong'
    "cbfb13341bbc7ddd4d14dadf84b69035",  # canary 'pong' JSON
    "fda6f552fc697f134a007e8fd6543187",  # genuine 384-char workflow result
}

POLL_SECS = 5
SESSION_GLOB = os.path.join(HOME, "agents", "agent-*", "sessions", "*.jsonl")


def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} {msg}\n")
    except Exception:
        pass


def md5(s):
    return hashlib.md5(s.encode("utf-8", errors="replace")).hexdigest()


def load_offsets():
    try:
        with open(OFFSETS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_offsets(off):
    tmp = OFFSETS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(off, f)
    os.replace(tmp, OFFSETS)


def strings_in(obj, out):
    """Collect all string values from a nested structure."""
    if isinstance(obj, str):
        if len(obj) >= 20:  # skip tiny strings; digests need real bodies
            out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            strings_in(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            strings_in(v, out)


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def main():
    os.makedirs(TRACE_DIR, exist_ok=True)
    offsets = load_offsets()
    # per-file rolling state (not persisted): recent item kinds, last user msg
    recent = {}   # path -> list of (kind, role)
    last_user = {}  # path -> (ts, md5, len)
    session_start = {}  # path -> first created_at ts
    item_count = {}  # path -> count
    log("live-trace daemon started")
    while True:
        try:
            poll(offsets, recent, last_user, session_start, item_count)
            save_offsets(offsets)
        except Exception as e:  # never die
            log(f"poll error: {e}")
        time.sleep(POLL_SECS)


def poll(offsets, recent, last_user, session_start, item_count):
    now = time.time()
    for path in glob.glob(SESSION_GLOB):
        try:
            st = os.stat(path)
        except OSError:
            continue
        if st.st_mtime < now - 600 and path in offsets and offsets[path] >= st.st_size:
            continue  # idle file, already fully read
        off = offsets.get(path, 0)
        if off > st.st_size:
            off = 0  # rotated/truncated
        try:
            with open(path, "rb") as f:
                f.seek(off)
                data = f.read()
                offsets[path] = f.tell()
        except OSError:
            continue
        if not data:
            continue
        agent_id = os.path.basename(os.path.dirname(os.path.dirname(path)))
        for raw in data.split(b"\n"):
            if not raw.strip():
                continue
            try:
                o = json.loads(raw)
            except Exception:
                continue
            handle_line(path, agent_id, o, now, recent, last_user,
                        session_start, item_count)


def handle_line(path, agent_id, o, now, recent, last_user, session_start,
                item_count):
    item = o.get("item") if isinstance(o.get("item"), dict) else {}
    itype = item.get("type", o.get("type", "?"))
    role = item.get("role")
    created = o.get("created_at")
    ts = parse_ts(created) if created else now

    item_count[path] = item_count.get(path, 0) + 1
    if path not in session_start and ts:
        session_start[path] = ts
    rk = recent.setdefault(path, [])
    rk.append(f"{itype}:{role}" if role else itype)
    if len(rk) > 15:
        del rk[0]

    if itype == "message" and role == "user":
        text = item.get("text", "")
        last_user[path] = (ts, md5(text), len(text))

    # refusal detection: hash every substantial string in the line
    found = None
    if itype in ("message", "commentary_text", "function_call_output"):
        strs = []
        strings_in(item if item else o, strs)
        for s in strs:
            d = md5(s)
            if d in REFUSAL_DIGESTS:
                found = (d, len(s))
                break
            # skip benign digests silently
    if not found:
        return

    digest, blen = found
    lu = last_user.get(path)
    latency_ms = int((ts - lu[0]) * 1000) if (lu and lu[0] and ts) else None
    incident = {
        "incident_id": uuid.uuid4().hex[:16],
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "session_file": path,
        "seq": o.get("seq"),
        "kind": itype,
        "role": role,
        "source": o.get("source"),
        "digest": digest,
        "body_len": blen,
        "prev_user_md5": lu[1] if lu else None,
        "prev_user_len": lu[2] if lu else None,
        "prev_user_at": (datetime.fromtimestamp(lu[0], timezone.utc).isoformat()
                         if lu and lu[0] else None),
        "latency_ms": latency_ms,
        "recent_item_kinds": list(rk),
        "session_items": item_count.get(path, 0),
        "session_age_s": int(ts - session_start[path]) if (
            path in session_start and ts) else None,
    }
    with open(INCIDENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(incident) + "\n")
    with open(LATEST, "w", encoding="utf-8") as f:
        json.dump(incident, f, indent=1)
    log(f"INCIDENT {incident['incident_id']} agent={agent_id[:8]} "
        f"digest={digest[:12]} len={blen} latency_ms={latency_ms}")


if __name__ == "__main__":
    main()
