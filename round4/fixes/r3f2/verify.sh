#!/bin/bash
set -uo pipefail

SQ="$ROUND4_ROOT/bin/spawn_queue.py"
rm -f "$ROUND4_ROOT/spawn_queue.jsonl" "$ROUND4_ROOT/spawn_queue_last"
python3 "$SQ" enqueue "probe-a" >/dev/null
python3 "$SQ" enqueue "probe-b" >/dev/null
python3 "$SQ" dequeue >/dev/null || exit 1
python3 "$SQ" dequeue >/dev/null 2>&1; rc=$?
[ "$rc" = "2" ] || { echo "expected throttle rc=2 got $rc"; exit 1; }
python3 -c "open('$ROUND4_ROOT/spawn_queue_last','w').write('1')"
python3 "$SQ" dequeue >/dev/null || exit 1
echo QUEUE_OK
