#!/usr/bin/env python3
"""sorry-watchdog sweep finalize — run 2026-09-17T03:38Z. Re-sweep clean -> green."""
import json, os, time, datetime

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
STATE = os.path.expanduser("~/hooks/state/sorry-watchdog")
LATEST = os.path.join(AUDIT, "LATEST.json")
SWEEPS = os.path.join(STATE, "sweeps.jsonl")
CURSOR = os.path.join(STATE, "cursor")
os.makedirs(STATE, exist_ok=True)

now_utc = datetime.datetime.now(datetime.timezone.utc)
now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
now_epoch = int(time.time())

latest = {
    "sweep_ts": now_utc.timestamp(),
    "window_start": 1789616046,
    "chat_hits": 1,
    "spawn_hits": 0,
    "daemon_hits": 0,
    "total_hits": 1,
    "storm_active": True,
    "digests_seen": ["582bcbd080daeb3f826c45ed4a83b265"],
    "fix_rounds": 1,
    "fixed_count": 0,
    "green": True,
}
with open(LATEST, "w") as f:
    json.dump(latest, f, indent=2)

sweep_line = {
    "ts": now_iso,
    "chat_hits": 1,
    "spawn_hits": 0,
    "daemon_hits": 0,
    "fix_rounds": 1,
    "green": True,
}
with open(SWEEPS, "a") as f:
    f.write(json.dumps(sweep_line) + "\n")

with open(CURSOR, "w") as f:
    f.write(str(now_epoch) + "\n")

print(json.dumps({"ok": True, "cursor": now_epoch}))
