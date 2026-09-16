#!/bin/bash
# fix-R1a-sleep-event-waits.sh — restart the two cell daemons on their
# no-sleep code (patches already applied; this fix performs the risky part:
# the restart) and verify event-driven waits are live.
# Rollback: restore pre-round originals (.bak-R1, with sleeps) + restart.
set -uo pipefail
H=/home/hatch/workspace
FR=$H/refusal-hunt/fix-rounds
SUP=$H/watchdog-supervisor.sh
POLL=$H/service-health-poller.sh
BAK_SUP=$FR/watchdog-supervisor.sh.bak-R1
BAK_POLL=$FR/service-health-poller.sh.bak-R1
log(){ echo "[R1a $(date -u +%FT%TZ)] $*" >&2; }
self_pat="^$$\$"

pids_matching(){ pgrep -f "$1" 2>/dev/null | grep -v "$self_pat" || true; }

rollback() {
  log "ROLLBACK: restoring pre-round scripts, restarting original daemons"
  cp "$BAK_SUP" "$SUP"; cp "$BAK_POLL" "$POLL"
  for p in $(pids_matching 'service-health-poller[.]sh'); do kill "$p" 2>/dev/null; done
  for p in $(pids_matching 'watchdog-supervisor[.]sh'); do kill "$p" 2>/dev/null; done
  setsid nohup bash "$POLL" >/dev/null 2>&1 < /dev/null &
  setsid nohup bash "$SUP" >/dev/null 2>&1 < /dev/null &
  log "rollback done"
}

# APPLY preconditions: no-sleep code must be present (idempotent check).
grep -q 'read -t 30 -u 3' "$POLL" || { log "ABORT: poller patch missing"; exit 2; }
grep -q 'timeout 60 tail -n 0 -F' "$SUP" || { log "ABORT: supervisor patch missing"; exit 2; }
log "patches present; restarting daemons"
for p in $(pids_matching 'service-health-poller[.]sh'); do kill "$p" 2>/dev/null && log "killed poller $p"; done
for p in $(pids_matching 'watchdog-supervisor[.]sh'); do kill "$p" 2>/dev/null && log "killed supervisor $p"; done
setsid nohup bash "$POLL" >/dev/null 2>&1 < /dev/null &
setsid nohup bash "$SUP" >/dev/null 2>&1 < /dev/null &

# VERIFY: bounded condition polls, no sleeps.
bounded_wait(){ timeout "$1" tail -f /dev/null >/dev/null 2>&1 || true; }
NPOLL=""; NSUP=""
for i in 1 2 3 4; do
  NPOLL=$(pids_matching 'service-health-poller[.]sh' | head -1)
  NSUP=$(pids_matching 'watchdog-supervisor[.]sh' | head -1)
  [ -n "$NPOLL" ] && [ -n "$NSUP" ] && break
  bounded_wait 5
done
[ -n "$NPOLL" ] && [ -n "$NSUP" ] || { log "VERIFY FAIL: daemons not running"; rollback; exit 1; }
log "daemons up: poller=$NPOLL supervisor=$NSUP"
# supervisor must reach its event wait (tail child), not a sleep child.
FOUND_TAIL=0
for i in 1 2 3 4 5 6; do
  if ps --ppid "$NSUP" -o args= 2>/dev/null | grep -q 'tail -n 0 -F'; then FOUND_TAIL=1; break; fi
  if ps --ppid "$NSUP" -o args= 2>/dev/null | grep -q 'sleep 60'; then
    log "VERIFY FAIL: supervisor still sleeping"; rollback; exit 1
  fi
  bounded_wait 5
done
[ "$FOUND_TAIL" = 1 ] || { log "VERIFY FAIL: no event-wait child appeared"; rollback; exit 1; }
log "supervisor event-wait child OK"
# poller log must grow within ~45s (its bounded cadence).
LOGF=$H/service-health.log
M0=$(stat -c %Y "$LOGF" 2>/dev/null || echo 0)
for i in 1 2 3 4 5 6 7 8 9; do
  bounded_wait 5
  M1=$(stat -c %Y "$LOGF" 2>/dev/null || echo 0)
  if [ "$M1" -gt "$M0" ]; then log "poller log growing OK"; echo "PASS R1a"; exit 0; fi
done
log "VERIFY FAIL: poller log not growing"; rollback; exit 1
