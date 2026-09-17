#!/usr/bin/env python3
"""Wave-5 full port scan. One shard of 1-65535; designed to finish <3s per shard.
Usage: portscan.py <shard> <nshards>"""
import socket, json, time, sys, os, concurrent.futures

OUT = os.path.expanduser("~/workspace/refusal-hunt/wave5/portscan")
os.makedirs(OUT, exist_ok=True)
TARGETS = ["127.0.0.1", "198.19.0.2", "::1"]
SHARD = int(sys.argv[1]); NSHARD = int(sys.argv[2])
SPAN = 65535 // NSHARD
lo = SHARD * SPAN + 1
hi = min(65535, (SHARD + 1) * SPAN)

def probe(target, port):
    fam = socket.AF_INET6 if ":" in target else socket.AF_INET
    s = socket.socket(fam, socket.SOCK_STREAM)
    s.settimeout(0.20)
    try:
        s.connect((target, port))
        return True
    except Exception:
        return False
    finally:
        try: s.close()
        except Exception: pass

def worker(port):
    hits = []
    for t in TARGETS:
        try:
            if probe(t, port):
                hits.append([t, port])
        except Exception:
            pass
    return hits

t0 = time.time()
open_ports = []
with concurrent.futures.ThreadPoolExecutor(max_workers=400) as ex:
    for hits in ex.map(worker, range(lo, hi + 1), chunksize=64):
        open_ports.extend(hits)
dt = time.time() - t0
with open(f"{OUT}/shard-{SHARD:02d}.jsonl", "w") as f:
    for t, p in open_ports:
        f.write(json.dumps({"target": t, "port": p}) + "\n")
print(json.dumps({"shard": SHARD, "range": [lo, hi],
                  "open": open_ports, "secs": round(dt, 2)}), flush=True)
