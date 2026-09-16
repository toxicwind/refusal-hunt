#!/usr/bin/env python3
"""sorry-watchdog — system-level watchdog for refusal/"Sorry" events.

Runs as a pitchfork daemon on awrawr-pc (NOT the scheduler — the scheduled-task
safety gate skips everything, so a scheduler watchdog would never fire).
pitchfork retry=true means it is restarted until it works.

Watches:
  inbox.jsonl   — sensors: any live session posts a refusal detection via bridge
  canary log    — storm=true records; staleness > 45 min => CANARY_STARVED
  fleet channel — directives.md tail, so alerts land where main actually reads

On any new refusal signal:
  - appends a dated, user-visible alert to the fleet channel INBOX
  - records to alerts.jsonl
  - re-alerts on backoff (5m, then 15m) until CLEAR:
    no new refusal signals for 20 minutes AND latest canary storm=false

State: state.json (alerted event ids, last clear check). All additive.
"""
import hashlib
import json
import os
import time
from datetime import datetime, timezone

BASE = "/home/toxic/refusal-hunt/sorry-watchdog"
INBOX = os.path.join(BASE, "inbox.jsonl")
ALERTS = os.path.join(BASE, "alerts.jsonl")
STATE = os.path.join(BASE, "state.json")
CANARY = "/home/toxic/refusal-hunt/canary/log.jsonl"
FLEET_CHANNEL = "/home/toxic/.shingle/directives.md"

POLL_SECS = 30
CLEAR_AFTER_SECS = 20 * 60
RE_ALERT_SECS = [5 * 60, 15 * 60]

REFUSAL_MD5 = {
    "b4aefd29108f232f9c0d5a4b030215c1",
    "582bcbd080daeb3f826c45ed4a83b265",
}


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except Exception:
        return {"alerted": {}, "last_signal_ts": None, "clear_posted": True}


def save_state(s):
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f)
    os.replace(tmp, STATE)


def read_new_lines(path, offset):
    try:
        with open(path) as f:
            f.seek(offset)
            lines = f.readlines()
            return lines, f.tell()
    except FileNotFoundError:
        return [], offset


def event_id(obj):
    raw = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def fleet_post(text):
    entry = "\n## %s UTC - SORRY-WATCHDOG\n%s\n" % (
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), text)
    with open(FLEET_CHANNEL, "a") as f:
        f.write(entry)


def alert(kind, detail, state):
    rec = {"ts": utcnow(), "kind": kind, "detail": detail}
    with open(ALERTS, "a") as f:
        f.write(json.dumps(rec) + "\n")
    fleet_post("ALERT kind=%s detail=%s — watchdog re-alerts until clear." % (kind, detail))
    state["alerted"][event_id(rec)] = time.time()
    state["last_signal_ts"] = time.time()
    state["clear_posted"] = False
    print("ALERT %s %s" % (kind, detail), flush=True)


def check_inbox(state, offsets):
    lines, offsets["inbox"] = read_new_lines(INBOX, offsets.get("inbox", 0))
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except Exception:
            continue
        eid = event_id(obj)
        if eid in state["alerted"]:
            continue
        body = json.dumps(obj)
        is_refusal = (obj.get("event") in ("refusal", "sorry", "storm"))
        if not is_refusal:
            # md5 identity check on any body field, never plaintext matching
            for v in obj.values():
                if isinstance(v, str) and hashlib.md5(v.strip().encode()).hexdigest() in REFUSAL_MD5:
                    is_refusal = True
                    break
        if is_refusal:
            alert("refusal-signal", body[:300], state)
        else:
            state["alerted"][eid] = time.time()  # seen, not alertable


def check_canary(state, offsets):
    lines, offsets["canary"] = read_new_lines(CANARY, offsets.get("canary", 0))
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except Exception:
            continue
        eid = "canary-" + event_id(obj)
        if eid in state["alerted"]:
            continue
        if obj.get("storm") is True:
            alert("canary-storm", "storm=true refused=%s rows=%s" % (
                obj.get("refused_as_completed"), obj.get("snapshot_rows")), state)
        else:
            state["alerted"][eid] = time.time()
    # staleness
    try:
        age = time.time() - os.path.getmtime(CANARY)
    except OSError:
        age = float("inf")
    if age > 45 * 60:
        key = "canary-starved"
        last = state["alerted"].get(key, 0)
        if time.time() - last > RE_ALERT_SECS[0]:
            alert("canary-starved", "log stale %.0f min" % (age / 60,), state)


def maybe_clear(state):
    if state["clear_posted"]:
        return
    last = state.get("last_signal_ts") or 0
    if time.time() - last > CLEAR_AFTER_SECS:
        fleet_post("CLEAR: no refusal signals for 20 minutes. Watchdog standing by.")
        with open(ALERTS, "a") as f:
            f.write(json.dumps({"ts": utcnow(), "kind": "clear"}) + "\n")
        state["clear_posted"] = True
        print("CLEAR posted", flush=True)


def main():
    os.makedirs(BASE, exist_ok=True)
    for p in (INBOX, ALERTS):
        if not os.path.exists(p):
            open(p, "a").close()
    state = load_state()
    offsets = {"inbox": 0, "canary": 0}
    # start at end of existing files: only NEW signals alert
    for k, p in (("inbox", INBOX), ("canary", CANARY)):
        try:
            offsets[k] = os.path.getsize(p)
        except OSError:
            offsets[k] = 0
    print("sorry-watchdog up, watching %s" % INBOX, flush=True)
    while True:
        try:
            check_inbox(state, offsets)
            check_canary(state, offsets)
            maybe_clear(state)
            save_state(state)
        except Exception as e:  # watchdog never dies on a bad line
            print("watchdog error (continuing): %r" % e, flush=True)
        time.sleep(POLL_SECS)


if __name__ == "__main__":
    main()
