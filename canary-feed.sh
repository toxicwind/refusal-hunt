#!/usr/bin/env bash
# canary-feed.sh — single-shot feeder for the awrawr-pc refusal canary.
#
# The missing link, made explicit: canary.py on awrawr-pc is a one-shot
# classifier; nothing invoked it on a schedule. This script closes one feed:
#   snapshot CSV -> bridge xfer put -> canary.py check --csv -> log.jsonl
# The awrawr-pc watchdog (sovereign/refusal-watchdog, inotify-driven) reacts
# to log.jsonl changes; it needs no cron and no scheduler gate.
#
# Contract: single shot, no loops, no sleep. Idempotent per snapshot file
# (canary.py refuses to double-record the same snapshot_id).
# Usage: canary-feed.sh /path/to/snapshot.csv
#
# Snapshot export (run via the muse.db tool, daemon-native Postgres):
#   SELECT spawn_id, status, md5(final_response) AS fr_md5,
#          length(final_response) AS fr_len, created_at AS created_epoch
#   FROM agent.subagent_spawns WHERE spawn_id > <last_seen> ORDER BY spawn_id
# Convert result rows to CSV with header:
#   spawn_id,status,fr_md5,fr_len,dur_s,created_epoch
# (fr_md5/fr_len empty for rows with no final_response yet; dur_s may be empty)
#
# Safe to run from anywhere, anytime. Additive: never touches a healthy chain.
set -uo pipefail

CSV="${1:?usage: canary-feed.sh /path/to/snapshot.csv}"
[ -f "$CSV" ] || { echo "[canary-feed] no such file: $CSV" >&2; exit 1; }

BRIDGE="$HOME/workspace/skills/awrawr-mcp/bin"
REMOTE_DIR="/home/toxic/refusal-hunt/canary"
BASE="$(basename "$CSV")"
TS="$(date -u +%Y%m%dT%H%M%SZ)"

# 1. Ship the snapshot (timestamped name => unique snapshot_id downstream)
python3 "$BRIDGE/xfer.py" --via auto put "$CSV" "$REMOTE_DIR/snapshot-$TS.csv" \
  || { echo "[canary-feed] xfer failed" >&2; exit 1; }

# 2. Classify on awrawr-pc (fail-fast: the check itself is sub-second work)
python3 "$BRIDGE/exec.py" --timeout 25 --argv \
  python3 /home/toxic/refusal-hunt/canary/canary.py check \
  --csv "$REMOTE_DIR/snapshot-$TS.csv" \
  || { echo "[canary-feed] canary check failed" >&2; exit 1; }

echo "[canary-feed] fed snapshot-$TS.csv OK"
