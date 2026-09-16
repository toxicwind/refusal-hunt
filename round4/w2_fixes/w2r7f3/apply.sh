#!/bin/bash
set -uo pipefail

SQ="$ROUND4_ROOT/bin/spawn_queue.py"
rm -f "$ROUND4_ROOT/spawn_queue.jsonl" "$ROUND4_ROOT/spawn_queue_seen" "$ROUND4_ROOT/spawn_queue_last"
i=1
while [ $i -le 6 ]; do
  python3 "$SQ" enqueue "w2-acceptance-pong-canary nonce=$i" >/dev/null || exit 1
  i=$((i+1))
done
n=$(python3 -c "print(len(open('$ROUND4_ROOT/spawn_queue.jsonl').read().splitlines()))")
[ "$n" = "6" ] || { echo "queue depth $n"; exit 1; }
echo "staged 6 acceptance canaries (NOT spawned: operator-gated during storm)"
