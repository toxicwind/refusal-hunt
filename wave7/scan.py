#!/usr/bin/env python3
"""Wave7 fast full-range TCP scan. Asyncio, per-attempt timeout 0.4s,
concurrency-capped. Writes open ports JSONL. Reconciliation with ss comes
after, from kernel tables."""
import asyncio, json, socket, sys, time

TARGETS = ["127.0.0.1"]
try:
    for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
        if ip not in TARGETS:
            TARGETS.append(ip)
except Exception:
    pass

PER_ATTEMPT = 0.4
CONC = 1500

async def probe(sem, host, port):
    async with sem:
        try:
            _, w = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=PER_ATTEMPT)
            w.close()
            return port
        except Exception:
            return None

async def scan_host(host):
    sem = asyncio.Semaphore(CONC)
    ports = range(1, 65536)
    t0 = time.monotonic()
    results = await asyncio.gather(
        *(probe(sem, host, p) for p in ports))
    dt = time.monotonic() - t0
    opens = sorted(p for p in results if p is not None)
    return host, opens, dt

async def main():
    out = "/home/hatch/workspace/refusal-hunt/wave7/open-ports.jsonl"
    with open(out, "w") as f:
        for host in TARGETS:
            host, opens, dt = await scan_host(host)
            f.write(json.dumps({"host": host, "open": opens,
                                "scan_s": round(dt, 2)}) + "\n")
            print(f"{host}: {len(opens)} open in {dt:.1f}s", flush=True)
    print("WROTE", out)

asyncio.run(main())
