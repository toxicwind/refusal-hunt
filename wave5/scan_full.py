#!/usr/bin/env python3
"""Wave-5 full TCP scan, single process. 1-65535 on 127.0.0.1 + 198.19.0.2.
Closed loopback ports RST immediately, so this is fast; backgrounded."""
import socket, json, time, os, concurrent.futures

OUT = os.path.expanduser("~/workspace/refusal-hunt/wave5")
TARGETS = ["127.0.0.1", "198.19.0.2"]

def probe(target, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.30)
    try:
        s.connect((target, port))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass

def worker(port):
    hits = [t for t in TARGETS if probe(t, port)]
    return (port, hits) if hits else None

t0 = time.time()
found = []
with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as ex:
    for r in ex.map(worker, range(1, 65536), chunksize=128):
        if r:
            found.append({"port": r[0], "targets": r[1]})
dt = time.time() - t0
found.sort(key=lambda d: d["port"])
with open(os.path.join(OUT, "open-ports.jsonl"), "w") as f:
    for d in found:
        f.write(json.dumps(d) + "\n")
summary = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "secs": round(dt, 2), "n_open": len(found), "open": found}
with open(os.path.join(OUT, "PORTSCAN-SUMMARY.json"), "w") as f:
    json.dump(summary, f, indent=1)
print(json.dumps({"secs": round(dt, 2), "n_open": len(found),
                  "ports": [(d["port"], d["targets"]) for d in found]}))
