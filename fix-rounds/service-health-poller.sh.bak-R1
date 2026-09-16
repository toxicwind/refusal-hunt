#!/bin/bash
# service-health-poller.sh — lightweight 30s metrics sampler for the restart watchdog.
# Appends one line per sample to ~/workspace/service-health.log. Single-instance.
# Dies with the cell on platform restarts (expected); the watchdog cron restarts it.
LOG="$HOME/workspace/service-health.log"
PIDFILE="$HOME/workspace/service-health-poller.pid"

if [ -f "$PIDFILE" ]; then
  OLD=$(cat "$PIDFILE" 2>/dev/null)
  if [ -n "$OLD" ] && kill -0 "$OLD" 2>/dev/null; then
    exit 0  # already running
  fi
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

while true; do
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  BOOT=$(cat /proc/sys/kernel/random/boot_id 2>/dev/null)
  MEM=$(free -m | awk '/^Mem:/{print $3"M_used/"$2"M_total/"$7"M_avail"}')
  DISK=$(df -h / | awk 'NR==2{print $5}')
  LOAD=$(cut -d' ' -f1 /proc/loadavg)
  DRSS=$(ps -o rss= -C hatch 2>/dev/null | awk '{s+=$1} END {if (NR>0) print int(s/1024)"M"; else print "n/a"}')
  echo "$TS boot=$BOOT mem=$MEM disk=$DISK load=$LOAD hatch_rss=$DRSS" >> "$LOG"
  sleep 30
done
