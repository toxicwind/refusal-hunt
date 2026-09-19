#!/usr/bin/env python3
"""ports_revalidate.py -- sharded TCP re-validation + ss reconcile (wave-8 task 4).

Additive cell-integrity monitor. Each run scans ONE shard of the 1-65535
port space (round-robin via state file) plus a full ss//proc-net-tcp
reconcile, so every 15-min hook poll stays cheap (<60s) while the full
space rotates through every 4 polls (~1h).

State: ~/workspace/refusal-hunt/state/ports/
  shard.idx        next shard to scan (0..N_SHARDS-1)
  baseline.json    {"listeners": [[ip, port], ...]} — additive baseline
  history.jsonl    one row per poll (append-only, never rewritten)

A "listener" = port seen OPEN by connect-scan OR present as LISTEN in
ss//proc/net/tcp. Wake condition (decided by the hook script from this
script's exit code / JSON): a listener NOT in baseline -> new listener.
Baseline starts empty (wave-7 truth: zero listeners); deltas are what matter.

Output: JSON {"shard": i, "open": [...], "ss_listen": [...], "reconciled": [...],
"new_vs_baseline": [...], "ms": t} ; exit 0 = no delta, exit 2 = delta.
"""
import asyncio
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import safe_write  # noqa: E402 -- append-exception guards (fail loud,
                   # keep prior good copy intact; debate 0220db63 slice 1)

STATE = os.path.expanduser("~/workspace/refusal-hunt/state/ports")
N_SHARDS = 4
PORTS_PER_SHARD = 65536 // N_SHARDS
CONCURRENCY = 1500
PER_ATTEMPT_S = 0.4


async def scan_port(sem, port):
    async with sem:
        try:
            fut = asyncio.open_connection("127.0.0.1", port)
            r, w = await asyncio.wait_for(fut, timeout=PER_ATTEMPT_S)
            try:
                # Discard the loopback simultaneous-open artifact: with a large
                # concurrent scan the kernel can hand the probe's source socket
                # the same port number as its target (ephemeral range overlaps
                # the scanned range), completing a self-connection that is not
                # a real listener.
                sockname = w.get_extra_info("sockname")
                phantom = bool(sockname) and sockname[1] == port
            except Exception:
                phantom = False
            w.close()
            try:
                await w.wait_closed()
            except Exception:
                pass
            return None if phantom else port
        except Exception:
            return None


async def scan_shard(lo, hi):
    sem = asyncio.Semaphore(CONCURRENCY)
    res = await asyncio.gather(*(scan_port(sem, p) for p in range(lo, hi)))
    return sorted(p for p in res if p is not None)


def ss_listeners():
    """LISTEN entries from ss; fall back to /proc/net/tcp 0A rows."""
    out = set()
    try:
        p = subprocess.run(["ss", "-tln", "-H"], capture_output=True,
                           text=True, timeout=10)
        for line in p.stdout.splitlines():
            f = line.split()
            if len(f) >= 4:
                addr = f[3]
                if ":" in addr:
                    try:
                        out.add(int(addr.rsplit(":", 1)[1]))
                    except ValueError:
                        pass
    except Exception:
        pass
    # /proc/net/tcp reconcile (authoritative even if ss is absent)
    try:
        for line in open("/proc/net/tcp").read().splitlines()[1:]:
            f = line.split()
            if len(f) >= 10 and f[3] == "0A":
                try:
                    out.add(int(f[1].rsplit(":", 1)[1], 16))
                except ValueError:
                    pass
    except Exception:
        pass
    return sorted(out)


def load_json(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def main():
    os.makedirs(STATE, exist_ok=True)
    t0 = time.monotonic()
    shard = load_json(os.path.join(STATE, "shard.idx"), 0) % N_SHARDS
    lo = 1 + shard * PORTS_PER_SHARD
    hi = lo + PORTS_PER_SHARD if shard < N_SHARDS - 1 else 65536
    open_ports = asyncio.run(scan_shard(lo, hi))
    ssl = ss_listeners()
    reconciled = sorted(set(open_ports) | set(ssl))
    baseline = load_json(os.path.join(STATE, "baseline.json"),
                         {"listeners": []})
    base = set(tuple(x) for x in baseline["listeners"])
    # baseline stores [port] pairs normalized to ("127.0.0.1", port)
    base_ports = {p for (_, p) in base} | {x[0] if isinstance(x, list) and len(x) == 1 else None for x in baseline["listeners"]}
    base_ports.discard(None)
    new = [p for p in reconciled if p not in base_ports]
    ms = int((time.monotonic() - t0) * 1000)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "shard": shard, "range": [lo, hi - 1],
           "open": open_ports, "ss_listen": ssl,
           "reconciled": reconciled, "new_vs_baseline": new, "ms": ms}
    # Append-exception guard: verified append + atomic shard rotation.
    # A torn shard.idx would rescan the wrong shard forever; a failed
    # history write must raise, never silently skip the poll row.
    safe_write.append_jsonl(os.path.join(STATE, "history.jsonl"), rec)
    safe_write.atomic_write_json(os.path.join(STATE, "shard.idx"),
                                 (shard + 1) % N_SHARDS)
    print(json.dumps(rec))
    return 2 if new else 0


if __name__ == "__main__":
    raise SystemExit(main())
