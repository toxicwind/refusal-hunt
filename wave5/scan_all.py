#!/usr/bin/env python3
"""Wave-5 scan driver: 32 shards, 4 concurrent, each <3s by design."""
import subprocess, concurrent.futures, json, os, sys, time

N = 32; PAR = 4
HERE = os.path.dirname(os.path.abspath(__file__))

def run(i):
    p = subprocess.run(
        [sys.executable, os.path.join(HERE, "portscan.py"), str(i), str(N)],
        capture_output=True, text=True, timeout=12)
    line = (p.stdout or "").strip().splitlines()
    return json.loads(line[-1]) if line else {"shard": i, "error": (p.stderr or "")[:200]}

t0 = time.time()
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=PAR) as ex:
    for r in ex.map(run, range(N)):
        results.append(r)
dt = time.time() - t0
all_open = {}
slow = []
for r in results:
    if r.get("secs", 0) > 3.0:
        slow.append({"shard": r["shard"], "secs": r["secs"]})
    for t, p in r.get("open", []):
        all_open.setdefault(t, set()).add(p)
summary = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "shards": N, "total_secs": round(dt, 2),
    "shards_over_3s": slow,
    "open": {t: sorted(v) for t, v in all_open.items()},
}
with open(os.path.join(HERE, "PORTSCAN-SUMMARY.json"), "w") as f:
    json.dump(summary, f, indent=1)
print(json.dumps(summary))
