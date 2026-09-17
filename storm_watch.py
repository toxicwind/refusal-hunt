#!/usr/bin/env python3
"""storm_watch.py — cell-side refusal-storm watcher (read-only + logging).

Polls agent session JSONLs for the two known canned-refusal digests and the
refusal ledger for new rows. Appends detections to storm_watch_log.jsonl and
writes repair manifests for fresh spawn-storm hits to fix-rounds/.

Repair itself runs through the saved `storm-fix-loop` workflow (the ungated
path); this watcher cannot launch workflows, so manifests are picked up by
the operator. No DB access from here — file-local only.

Polling uses the sanctioned isleep primitive (no sleep/timeout binaries).
Start: setsid nohup python3 storm_watch.py >> storm_watch.out 2>&1 < /dev/null &
Stop: isleep interrupt --name storm-watch  (or kill the python pid)
"""
import hashlib, json, os, glob, subprocess, sys, time

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "workspace", "refusal-hunt")
STATE = os.path.join(BASE, "storm_watch_state.json")
LOG = os.path.join(BASE, "storm_watch_log.jsonl")
FIXDIR = os.path.join(BASE, "fix-rounds")
ISLEEP = os.path.join(HOME, "workspace", "bin", "isleep")
POLL_SECS = 300

CHAT96 = "582bcbd080daeb3f826c45ed4a83b265"
SPAWN384 = "b4aefd29108f232f9c0d5a4b030215c1"
KNOWN = {CHAT96: "chat96", SPAWN384: "spawn384"}

def load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {"offsets": {}, "ledger_max_ts": None, "started": None}

def save_state(s):
    tmp = STATE + ".tmp"
    json.dump(s, open(tmp, "w"))
    os.replace(tmp, STATE)

def log_event(ev):
    ev["watch_ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(LOG, "a") as f:
        f.write(json.dumps(ev) + "\n")

def md5_str(s):
    return hashlib.md5(s.encode("utf-8", "replace")).hexdigest()

def scan_sessions(state):
    """Scan only new bytes of each session JSONL for digest hits."""
    new_hits = []
    for fp in glob.glob(os.path.join(HOME, "agents", "*", "sessions", "*.jsonl")):
        try:
            size = os.path.getsize(fp)
        except OSError:
            continue
        off = state["offsets"].get(fp, 0)
        if size < off:  # rotated/truncated
            off = 0
        if size == off:
            continue
        hits = {v: 0 for v in KNOWN.values()}
        try:
            with open(fp, "r", errors="replace") as f:
                f.seek(off)
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        obj = json.loads(ln)
                    except Exception:
                        continue
                    stack = [obj]
                    while stack:
                        o = stack.pop()
                        if isinstance(o, dict):
                            stack.extend(o.values())
                        elif isinstance(o, list):
                            stack.extend(o)
                        elif isinstance(o, str) and len(o) > 90:
                            h = md5_str(o)
                            if h in KNOWN:
                                hits[KNOWN[h]] += 1
        except OSError:
            continue
        state["offsets"][fp] = size
        for kind, n in hits.items():
            if n:
                new_hits.append({"kind": kind, "session_file": fp, "new_rows": n})
    return new_hits

def check_ledger(state):
    """Report if the ledger parquet gained rows (max created_at advanced)."""
    lp = os.path.join(BASE, "ledger", "anomalies.parquet")
    try:
        import pyarrow.parquet as pq
        t = pq.read_table(lp, columns=["created_at"])
        mx = t.to_pandas()["created_at"].max()
        mxs = str(mx)
    except Exception as e:
        return {"ledger_error": str(e)[:120]}
    prev = state.get("ledger_max_ts")
    state["ledger_max_ts"] = mxs
    if prev and mxs > prev:
        return {"ledger_advanced": True, "prev_max": prev, "new_max": mxs}
    return {"ledger_advanced": False, "max": mxs}

def write_manifest(hits):
    os.makedirs(FIXDIR, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    mp = os.path.join(FIXDIR, "manifest-%s.json" % ts)
    json.dump({"ts": ts, "note": "fresh spawn-storm digest hits; enrich with prompts via DB before launching storm-fix-loop",
               "hits": hits}, open(mp, "w"), indent=2)
    return mp

def main():
    state = load_state()
    if not state.get("started"):
        state["started"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        save_state(state)
    log_event({"event": "watcher_started", "poll_secs": POLL_SECS})
    while True:
        try:
            hits = scan_sessions(state)
            ledger = check_ledger(state)
            save_state(state)
            for h in hits:
                log_event({"event": "digest_hits", **h})
            if ledger.get("ledger_advanced"):
                log_event({"event": "ledger_advanced", **ledger})
            spawn_hits = [h for h in hits if h["kind"] == "spawn384"]
            if spawn_hits:
                mp = write_manifest(spawn_hits)
                log_event({"event": "manifest_written", "path": mp, "n": len(spawn_hits)})
        except Exception as e:
            log_event({"event": "poll_error", "error": str(e)[:200]})
        subprocess.run([ISLEEP, str(POLL_SECS), "--name", "storm-watch"])

if __name__ == "__main__":
    main()
