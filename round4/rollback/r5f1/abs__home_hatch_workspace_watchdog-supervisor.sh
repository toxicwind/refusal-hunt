#!/bin/bash
# watchdog-supervisor.sh — gate-proof cell-side supervisor (grey iterative cover).
# The scheduled-task safety review is blanket-skipping the scheduler watchdogs
# (service-restart-watchdog, sidechat-watch-*, squawk-ws-client-watchdog, ...),
# all reporting status "succeeded" while doing nothing. This loop does the
# service-restart-watchdog's job as a plain detached process, which never
# passes through the scheduler gate at all.
# Dies with the cell (expected); restart it from cell-boot-resume.sh.
# Alerts go to the supervisor's own alert log; the next live agent session
# surfaces them. No chat delivery from here — that path is what is broken.

LOG="$HOME/workspace/service-health.log"
STATE="$HOME/workspace/service-health.state"
ALERT="$HOME/workspace/watchdog-alerts.log"
POLLER="$HOME/workspace/service-health-poller.sh"

log_alert() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$ALERT"; }

# boot: on first run after a cell death, STATE holds the pre-restart boot_id.
while true; do
  # 1. Self-heal the sampler
  if ! pgrep -f "service-health-poller.sh" >/dev/null 2>&1; then
    setsid nohup bash "$POLLER" >/dev/null 2>&1 < /dev/null &
    log_alert "HEAL restarted service-health-poller.sh (was dead)"
  fi

  # 2. Restart detection
  if [ -f "$LOG" ]; then
    LATEST_BOOT=$(tail -1 "$LOG" | sed -n 's/.*boot=\([0-9a-f-]*\).*/\1/p')
    if [ -n "$LATEST_BOOT" ]; then
      if [ ! -f "$STATE" ]; then
        echo "$LATEST_BOOT" > "$STATE"
        log_alert "STATE init boot=$LATEST_BOOT"
      else
        OLD=$(cat "$STATE")
        if [ "$OLD" != "$LATEST_BOOT" ]; then
          FIRST_NEW=$(grep -m1 "boot=$LATEST_BOOT" "$LOG" | cut -c1-20)
          log_alert "RESTART detected old_boot=$OLD new_boot=$LATEST_BOOT first_seen=${FIRST_NEW}Z"
          echo "$LATEST_BOOT" > "$STATE"
        fi
      fi
      # 3. Pressure check on latest line
      LINE=$(tail -1 "$LOG")
      AVAIL=$(echo "$LINE" | sed -n 's/.*\/\([0-9]*\)M_avail.*/\1/p')
      DISK=$(echo "$LINE" | sed -n 's/.*disk=\([0-9]*\)%.*/\1/p')
      if [ -n "$AVAIL" ] && [ "$AVAIL" -lt 1024 ]; then
        log_alert "PRESSURE mem_avail=${AVAIL}M < 1024M :: $LINE"
      fi
      if [ -n "$DISK" ] && [ "$DISK" -ge 90 ]; then
        log_alert "PRESSURE disk=${DISK}% >= 90% :: $LINE"
      fi
      # 4b. Canary freshness: the awrawr-pc canary only classifies when fed.
      # canary-feed.sh is the feeder (single-shot, any session can run it).
      # If the log goes stale while the last state was storm=true, alert so a
      # live session feeds it. Fail-fast bridge probe; a dead bridge is itself
      # an alert, not a reason to spin.
      CANARY_LOG_MTIME=$(timeout 10 python3 "$HOME/workspace/skills/awrawr-mcp/bin/exec.py" \
        --timeout 8 'stat -c %Y /home/toxic/refusal-hunt/canary/log.jsonl' 2>/dev/null | tail -1)
      if [ -n "$CANARY_LOG_MTIME" ] && [ "$CANARY_LOG_MTIME" -eq "$CANARY_LOG_MTIME" ] 2>/dev/null; then
        NOW=$(date +%s)
        STALE_FOR=$(( NOW - CANARY_LOG_MTIME ))
        if [ "$STALE_FOR" -gt 2700 ]; then
          log_alert "CANARY_STARVED log.jsonl stale ${STALE_FOR}s (>45min) :: run: ~/workspace/refusal-hunt/canary-feed.sh <snapshot.csv>"
        fi
      else
        # Throttle the unreachable alert: at most one per 30min, not per tick.
        LAST_PROBE_ALERT="$HOME/workspace/.canary-probe-alert-epoch"
        NOW_EPOCH=$(date +%s)
        PREV_EPOCH=$(cat "$LAST_PROBE_ALERT" 2>/dev/null || echo 0)
        if [ $(( NOW_EPOCH - PREV_EPOCH )) -gt 1800 ]; then
          log_alert "CANARY_PROBE bridge unreachable or log unreadable (single probe, not retried)"
          echo "$NOW_EPOCH" > "$LAST_PROBE_ALERT"
        fi
      fi
      # 4. Hygiene
      LINES=$(wc -l < "$LOG")
      if [ "$LINES" -gt 20000 ]; then
        tail -10000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
        log_alert "HYGIENE trimmed log to 10000 lines"
      fi
    fi
  fi
  # Bounded event wait (no fixed sleep): wake when the supervised log grows
  # (the real condition this loop watches), or after 60s at the latest.
  timeout 60 tail -n 0 -F "$LOG" >/dev/null 2>&1 || true
done
