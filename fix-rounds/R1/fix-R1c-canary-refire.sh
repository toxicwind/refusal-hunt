#!/bin/bash
# fix-R1c-canary-refire.sh — live end-to-end canary feed RIGHT NOW:
# snapshot CSV -> bridge xfer -> canary.py check -> log.jsonl, then verify the
# watcher-visible record exists. Rollback: none (log is append-only by design;
# a feed record is data, not state).
set -uo pipefail
UR=/home/hatch/workspace/bin/ur
BRIDGE=/home/hatch/workspace/skills/awrawr-mcp/bin/exec.py
CANLOG=/home/toxic/refusal-hunt/canary/log.jsonl
CSV=/home/hatch/workspace/refusal-hunt/snapshot-20260916T0545Z.csv
FEED=/home/hatch/workspace/refusal-hunt/canary-feed.sh
log(){ echo "[R1c $(date -u +%FT%TZ)] $*" >&2; }

[ -f "$CSV" ] || { log "ABORT: snapshot CSV missing"; exit 2; }
BEFORE=$(python3 "$BRIDGE" --timeout 25 --argv tail -1 "$CANLOG" 2>/dev/null)
log "last canary record before feed: $(echo "$BEFORE" | head -c 160)"
$UR bash "$FEED" "$CSV" || { log "FEED FAILED"; exit 1; }
AFTER=$(python3 "$BRIDGE" --timeout 25 --argv tail -1 "$CANLOG" 2>/dev/null)
[ -n "$AFTER" ] && [ "$AFTER" != "$BEFORE" ] || { log "VERIFY FAIL: no new canary record"; exit 1; }
echo "$AFTER" | grep -q '"storm"' || { log "VERIFY FAIL: record lacks storm field"; exit 1; }
log "new record: $(echo "$AFTER" | head -c 220)"
echo "PASS R1c"
