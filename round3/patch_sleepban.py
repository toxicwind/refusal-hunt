#!/usr/bin/env python3
"""One-shot: patch round_runner.py — sleep ban + bridge kind."""
import io
import shutil

p = '/home/hatch/workspace/refusal-hunt/round3/round_runner.py'
shutil.copy2(p, p + '.bak-sleepban')
s = io.open(p, encoding='utf-8').read()

old_job_result = '''def job_result(jid: str, timeout_s: int = 600) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        rc, out = sh_bridge(f"{JOB[0]} status {jid}", timeout=60)
        if "status:     done" in out:
            _, res = sh_bridge(f"{JOB[0]} result {jid}", timeout=60)
            return {"status": "done", "result": res}
        if "status:     failed" in out:
            _, log = sh_bridge(f"{JOB[0]} log {jid}", timeout=60)
            return {"status": "failed", "log": log[-2000:]}
        time.sleep(5)
    return {"status": "timeout"}'''

new_job_result = '''def _job_result_legacy_blocking(jid: str, timeout_s: int = 600) -> dict:
    """DEPRECATED 2026-09-16: used time.sleep(5) blocking loop.

    Banned by standing order (no sleep/timeout binaries, no blocking
    sleeps). Kept for provenance only -- never call. Use job_result_async.
    """
    raise RuntimeError("legacy blocking poller is banned; use job_result_async")


async def job_result_async(jid: str, timeout_s: int = 600) -> dict:
    """Poll-await a fleet job: cooperative waits, bounded by wait_for.

    No time.sleep, no sleep/timeout binaries. Every bridge round-trip is
    wrapped in asyncio.wait_for (try/catch timeout); the inter-poll wait is
    a cooperative asyncio.sleep inside wait_for so the loop stays live and
    the deadline is enforced by exception, not by a timer process.
    """
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout_s

    async def bridge(cmd: str, op_timeout: int = 60) -> tuple:
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(POOL, sh_bridge, cmd, op_timeout),
                timeout=op_timeout + 5)
        except asyncio.TimeoutError:
            return -2, "TIMEOUT awaiting bridge response"
        except Exception as e:
            return -1, f"{type(e).__name__}: {e}"

    while True:
        if loop.time() >= deadline:
            return {"status": "timeout"}
        rc, out = await bridge(f"{JOB[0]} status {jid}")
        if rc == -2:
            return {"status": "bridge-timeout"}
        if "status:     done" in out:
            rc2, res = await bridge(f"{JOB[0]} result {jid}")
            if rc2 == -2:
                return {"status": "result-timeout"}
            return {"status": "done", "result": res}
        if "status:     failed" in out:
            rc2, log = await bridge(f"{JOB[0]} log {jid}")
            if rc2 == -2:
                return {"status": "log-timeout"}
            return {"status": "failed", "log": log[-2000:]}
        try:
            await asyncio.wait_for(asyncio.sleep(5), timeout=deadline - loop.time())
        except asyncio.TimeoutError:
            return {"status": "timeout"}'''

assert old_job_result in s, 'job_result block not found'
s = s.replace(old_job_result, new_job_result)

old_branch = '''                jr = await loop.run_in_executor(POOL, job_result, jid,
                                                    fix.get("timeout", 600))'''
new_branch = '''                jr = await job_result_async(jid, fix.get("timeout", 600))'''
assert old_branch in s, 'job branch not found'
s = s.replace(old_branch, new_branch)

old_cell_kind = '''            if fix["kind"] == "cell":
                rc, out = await loop.run_in_executor(
                    POOL, sh_cell, fix["run"], fix.get("timeout", 120))
                rec.update({"rc": rc, "out": out[-1500:]})
                ok = rc == 0'''
new_cell_kind = old_cell_kind + '''
            elif fix["kind"] == "bridge":
                rc, out = await loop.run_in_executor(
                    POOL, sh_bridge, fix["run"], fix.get("timeout", 120))
                rec.update({"rc": rc, "out": out[-1500:]})
                ok = rc == 0'''
assert old_cell_kind in s, 'cell kind not found'
s = s.replace(old_cell_kind, new_cell_kind)

old_verify = '''                if vkind == "cell":
                    rc, out = await loop.run_in_executor(
                        POOL, sh_cell, fix["verify"]["run"], 60)
                    ok = rc == 0 and fix["verify"].get("expect", "") in out
                    rec["verify_out"] = out[-800:]'''
new_verify = old_verify + '''
                elif vkind == "bridge":
                    rc, out = await loop.run_in_executor(
                        POOL, sh_bridge, fix["verify"]["run"], 60)
                    ok = rc == 0 and fix["verify"].get("expect", "") in out
                    rec["verify_out"] = out[-800:]'''
assert old_verify in s, 'verify block not found'
s = s.replace(old_verify, new_verify)

old_doc = "asyncio + ThreadPoolExecutor; nest_asyncio unavailable in this cell,\nstdlib suffices \u2014 no nested loop needed"
assert old_doc in s, 'docstring not found'
s = s.replace(
    old_doc,
    "asyncio + ThreadPoolExecutor; poll-await style \u2014 no time.sleep,\nno sleep/timeout binaries; bounded waits via asyncio.wait_for try/catch")

io.open(p, 'w', encoding='utf-8').write(s)
print('runner patched OK')
