#!/bin/bash
set -uo pipefail

cat > "$ROUND4_ROOT/bin/spawn_queue.py" <<'PYEOF'
#!/usr/bin/env python3
"""FIFO spawn queue with min-interval throttle (storm-autocorrelation guard).
Usage: spawn_queue.py enqueue '<prompt>' | dequeue"""
import json, os, sys, time
R = os.environ["ROUND4_ROOT"]
Q = R + "/spawn_queue.jsonl"
LAST = R + "/spawn_queue_last"
def load_cfg():
    try:
        return json.load(open(R + "/spawn_throttle.json"))
    except Exception:
        return {"min_interval_s": 90}
def main():
    cmd = sys.argv[1]
    if cmd == "enqueue":
        open(Q, "a").write(json.dumps({"t": time.time(), "prompt": sys.argv[2]}) + "\n")
        print("enqueued"); return
    if cmd == "dequeue":
        cfg = load_cfg(); now = time.time()
        try: last = float(open(LAST).read())
        except Exception: last = 0
        if now - last < cfg["min_interval_s"]:
            print("throttled: wait %ds" % int(cfg["min_interval_s"] - (now - last)))
            sys.exit(2)
        if not os.path.exists(Q): print("empty"); sys.exit(3)
        lines = open(Q).read().splitlines()
        if not lines: print("empty"); sys.exit(3)
        first, rest = lines[0], lines[1:]
        open(Q, "w").write("\n".join(rest) + ("\n" if rest else ""))
        open(LAST, "w").write(str(now))
        print(first); return
    sys.exit(4)
main()
PYEOF
chmod +x "$ROUND4_ROOT/bin/spawn_queue.py"
echo "queue written"
