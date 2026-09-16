#!/usr/bin/env python3
"""Smoke test: no-backoff poll-await job_result_async against a trivial PC job.

Uses durable unique scratch (no /tmp) and the runner's own job_submit +
job_result_async. Reports submit -> poll transitions -> terminal status.
"""
import asyncio
import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round_runner as rr

SCRATCH = os.path.expanduser(
    "~/workspace/refusal-hunt/round3/scratch/smoke-" + uuid.uuid4().hex[:8])
os.makedirs(SCRATCH, exist_ok=True)
LOCAL_SPEC = os.path.join(SCRATCH, "spec_smoke.json")
PC_SPEC = "/home/toxic/refusal-hunt/round3/spec_smoke.json"


async def main():
    spec = {"name": "smoke-echo", "cmd": ["echo", "smoke-ok"],
            "cwd": "/home/toxic/refusal-hunt/round3",
            "env": {}, "heartbeat_interval": 60, "timeout": 120}
    with open(LOCAL_SPEC, "w") as f:
        json.dump(spec, f)
    rc, out = rr.sh_bridge(
        "cat > %s <<'EOF'\n%s\nEOF\ncat %s" % (PC_SPEC, open(LOCAL_SPEC).read(), PC_SPEC))
    print("spec write rc:", rc, "tail:", (out or "")[-100:])
    if rc != 0:
        print("SPEC WRITE FAILED")
        return
    t0 = time.time()
    loop = asyncio.get_event_loop()
    rc, jid = await loop.run_in_executor(rr.POOL, rr.job_submit, PC_SPEC)
    print("submit rc:", rc, "jid:", jid)
    if rc != 0 or not jid:
        print("SUBMIT FAILED")
        return
    res = await rr.job_result_async(jid, timeout_s=180)
    dt = time.time() - t0
    print("poll-await result status:", res.get("status"), "(%.1fs)" % dt)
    print("result tail:", str(res.get("result", res.get("log", "")))[-200:])


asyncio.get_event_loop().run_until_complete(main())
