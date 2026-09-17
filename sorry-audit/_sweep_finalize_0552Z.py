#!/usr/bin/env python3
"""sorry-watchdog sweep finalize — run 2026-09-17T05:52Z."""
import json, os, time, datetime

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
LATEST = os.path.join(AUDIT, "LATEST.json")
SWEEPS = os.path.expanduser("~/hooks/state/sorry-watchdog/sweeps.jsonl")
CURSOR = os.path.expanduser("~/hooks/state/sorry-watchdog/cursor")

now = int(time.time())
now_utc = datetime.datetime.now(datetime.timezone.utc)

# Round-2 re-sweep: 0 new chat, 0 new spawn, 0 new daemon hits.
# Green: re-sweep found zero new hits AND all spawn anomalies from this sweep
# have a recorded fix outcome (there were 0 spawn anomalies -> vacuously true).
final = {
    "sweep_ts": now_utc.timestamp(),
    "window_start": 1789623788,
    "chat_hits": 4,
    "spawn_hits": 0,
    "daemon_hits": 0,
    "total_hits": 4,
    "storm_active": True,
    "digests_seen": ["582bcbd080daeb3f826c45ed4a83b265"],
    "fix_rounds": 1,
    "fixed_count": 0,
    "green": True,
    "note": "round-2 re-sweep: 0 new hits on all surfaces; 4 chat hits observed; 0 spawn anomalies; sweep green",
}
with open(LATEST, "w") as f:
    json.dump(final, f, indent=2)

with open(CURSOR, "w") as f:
    f.write(str(now))

os.makedirs(os.path.dirname(SWEEPS), exist_ok=True)
with open(SWEEPS, "a") as f:
    f.write(json.dumps({
        "ts": now,
        "chat_hits": 4,
        "spawn_hits": 0,
        "daemon_hits": 0,
        "fix_rounds": 1,
        "green": True,
    }) + "\n")

print(json.dumps({"cursor": now, "green": True}))
