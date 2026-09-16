#!/bin/bash
set -uo pipefail

SQ="$ROUND4_ROOT/bin/spawn_queue.py"
rm -f "$ROUND4_ROOT/spawn_queue.jsonl" "$ROUND4_ROOT/spawn_queue_last" "$ROUND4_ROOT/spawn_queue_seen"
python3 "$SQ" enqueue "w2-dedup-probe" >/dev/null || exit 1
python3 "$SQ" enqueue "w2-dedup-probe" >/dev/null 2>&1; rc=$?
[ "$rc" = "5" ] || { echo "expected rc=5 got $rc"; exit 1; }
python3 "$SQ" enqueue "w2-dedup-probe-other" >/dev/null || exit 1
echo QUEUE_DEDUP_OK
