#!/usr/bin/env bash
# sorry_watchdog_sup.sh -- supervisor for the sorry watchdog.
# Restarts the daemon if the process dies: restarted until it works.
# No sleeps: restart is immediate; a timestamp guard prevents hot-spin
# (>5 restarts within 60s => fail loud instead of spinning).
set -u
BASE="/home/hatch/workspace/refusal-hunt"
BIN="$BASE/bin/sorry_watchdog.py"
LOG="$BASE/sorry_watchdog.log"
GUARD="$BASE/sorry_watchdog.restarts"

utc() { date -u +%FT%TZ; }

while true; do
  now=$(date +%s)
  echo "$now" >> "$GUARD"
  # keep only the last 60s of restart timestamps
  awk -v n="$now" '$1 > n-60' "$GUARD" > "$GUARD.tmp" && mv "$GUARD.tmp" "$GUARD"
  count=$(wc -l < "$GUARD")
  if [ "$count" -gt 5 ]; then
    echo "$(utc) supervisor: $count restarts in 60s, failing loud" >> "$LOG"
    exit 1
  fi
  echo "$(utc) supervisor: starting watchdog (restart #$count)" >> "$LOG"
  /usr/bin/python3 "$BIN" >> "$LOG" 2>&1
  echo "$(utc) supervisor: watchdog exited code $?, restarting" >> "$LOG"
done
