#!/usr/bin/env python3
"""fix-rounds/driver.py — parallel fix-round orchestrator.

Runs every fix-*.sh in a round dir CONCURRENTLY via asyncio.gather (nested
gather pattern; nest_asyncio applied so loops can nest inside notebooks or
other running loops). Each fix script is self-rollback-able:
  exit 0 = PASS (snapshotted, applied, verified)
  exit 1 = FAIL (rolled back inside the script)
The driver never touches another fix's state: one writer per fix, no shared
mutation. Results -> stdout JSON + ROUNDLOG.md append.
"""
import asyncio
import glob
import json
import os
import sys
import time

try:
    import nest_asyncio  # preferred: parallel rounds may nest event loops
    nest_asyncio.apply()
    NEST = True
    NEST_VER = getattr(nest_asyncio, "__version__", "unknown")
except ImportError:
    # Fallback (documented R4 behavior): stdlib asyncio alone. nest_asyncio
    # only matters when an event loop is already running; the driver is
    # top-level asyncio.run, so gather concurrency is unchanged.
    NEST = False
    NEST_VER = "stdlib-fallback"

UR = "/home/hatch/workspace/bin/ur"


async def run_fix(script, timeout):
    name = os.path.basename(script)
    t0 = time.monotonic()
    proc = await asyncio.create_subprocess_exec(
        UR, "bash", script,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout)
        rc = proc.returncode
    except asyncio.TimeoutError:
        proc.kill()
        out, _ = await proc.communicate()
        rc = 124
    dt = time.monotonic() - t0
    tail = out.decode(errors="replace")[-1200:]
    return {"fix": name, "rc": rc, "secs": round(dt, 1),
            "result": "PASS" if rc == 0 else ("TIMEOUT" if rc == 124 else "FAIL"),
            "tail": tail}


async def arun(round_dir, timeout):
    scripts = sorted(glob.glob(os.path.join(round_dir, "fix-*.sh")))
    if not scripts:
        return []
    # Nested parallelism: the round's fixes race concurrently; inside each
    # fix, snapshot->apply->verify->rollback stays strictly sequenced.
    return await asyncio.gather(*(run_fix(s, timeout) for s in scripts))


def main():
    round_dir = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 180
    t0 = time.monotonic()
    results = asyncio.run(arun(round_dir, timeout))
    wall = round(time.monotonic() - t0, 1)
    npass = sum(1 for r in results if r["result"] == "PASS")
    summary = {"round": os.path.basename(round_dir), "wall_secs": wall,
               "nest_asyncio": NEST, "nest_ver": NEST_VER, "fixes": results,
               "pass": npass, "fail": len(results) - npass}
    print(json.dumps(summary, indent=1))
    logp = os.path.join(os.path.dirname(round_dir.rstrip("/")), "ROUNDLOG.md")
    with open(logp, "a") as f:
        f.write("\n## %s UTC - round %s: %d/%d PASS in %ss (parallel, nest_asyncio=%s)\n"
                % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   summary["round"], npass, len(results), wall, NEST))
        for r in results:
            f.write("- %s: %s (rc=%s, %ss)\n" % (r["fix"], r["result"], r["rc"], r["secs"]))

    jp = os.path.join(os.path.dirname(round_dir.rstrip("/")), "journal.jsonl")
    with open(jp, "a") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            **summary}) + "\n")


if __name__ == "__main__":
    main()
