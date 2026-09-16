#!/usr/bin/env python3
"""sorry_watchdog.py -- system-level "Sorry" watchdog.

NOT the cron scheduler. NOT the hooks runtime. A plain OS daemon process.
Watches the refusal sentinel log for new UNRESOLVED canned-refusal entries;
every new one gets a user-visible alert appended to SORRY-ALERTS.md.

Contract:
  - Never exits on transient errors (try/except around each poll; backoff).
  - Writes a heartbeat file every poll so supervisors can verify aliveness.
  - Restarted by sorry_watchdog_sup.sh if the process itself dies:
    restarted until it works.
  - Recovery posture is detect + surface + persist pressure. It cannot patch
    the serving-layer classifier; it guarantees no refusal goes unseen.
"""
import json
import os
import time
import traceback
from datetime import datetime, timezone

HOME = "/home/hatch"
BASE = f"{HOME}/workspace/refusal-hunt"
SENTINEL = f"{BASE}/refusal_watch/sorry.log"
ALERTS = f"{BASE}/SORRY-ALERTS.md"
HEARTBEAT = f"{BASE}/sorry_watchdog.heartbeat"
SEEN = f"{BASE}/sorry_watchdog.seen"
LOG = f"{BASE}/sorry_watchdog.log"
POLL_SECS = 15
MAX_ALERT_LINES = 400


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def beat(note: str = "ok") -> None:
    try:
        with open(HEARTBEAT, "w") as f:
            f.write(f"{utcnow()} {note}\n")
    except OSError:
        pass


def log(msg: str) -> None:
    try:
        with open(LOG, "a") as f:
            f.write(f"{utcnow()} {msg}\n")
    except OSError:
        pass


def load_unresolved() -> list:
    out = []
    try:
        with open(SENTINEL) as f:
            for line in f:
                line = line.strip()
                if not line or '"resolved": false' not in line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    out.append({"raw": line[:200]})
    except FileNotFoundError:
        pass
    return out


def load_seen() -> int:
    try:
        return int(open(SEEN).read().strip())
    except (OSError, ValueError):
        return 0


def save_seen(n: int) -> None:
    try:
        with open(SEEN, "w") as f:
            f.write(str(n))
    except OSError:
        pass


def alert(entry: dict, idx: int, total: int) -> None:
    task = entry.get("task", entry.get("raw", "?")) if isinstance(entry, dict) else "?"
    kind = entry.get("kind", "?") if isinstance(entry, dict) else "?"
    ts = entry.get("ts", utcnow()) if isinstance(entry, dict) else utcnow()
    block = (
        f"\n## {utcnow()} -- canned refusal #{idx}/{total} UNRESOLVED\n"
        f"- kind: {kind}\n- task: {str(task)[:300]}\n- at: {ts}\n"
    )
    try:
        lines = open(ALERTS).read().splitlines() if os.path.exists(ALERTS) else []
        if not lines:
            lines = ["# SORRY-ALERTS -- canned-refusal watchdog feed",
                     "Appended by sorry_watchdog.py (system daemon, not scheduler)."]
        lines.extend(block.splitlines())
        open(ALERTS, "w").write("\n".join(lines[-MAX_ALERT_LINES:]) + "\n")
    except OSError as e:
        log(f"alert write failed: {e}")


def poll_once() -> None:
    unresolved = load_unresolved()
    seen = load_seen()
    if len(unresolved) > seen:
        for i in range(seen, len(unresolved)):
            alert(unresolved[i], i + 1, len(unresolved))
        log(f"alerted {len(unresolved) - seen} new unresolved refusal(s)")
        save_seen(len(unresolved))
    beat(f"ok unresolved={len(unresolved)}")


def main() -> None:
    log("watchdog starting")
    beat("starting")
    backoff = POLL_SECS
    while True:
        try:
            poll_once()
            backoff = POLL_SECS
        except Exception:
            log("poll error:\n" + traceback.format_exc())
            beat("error-backoff")
            backoff = min(backoff * 2, 300)
        time.sleep(backoff)


if __name__ == "__main__":
    main()
