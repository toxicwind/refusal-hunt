#!/usr/bin/env python3
"""round_runner.py — recursive 8-round refusal-storm repair orchestrator.

Each round = 3 fixes, ordered by confidence. Fixes run in PARALLEL within a
round (asyncio + ThreadPoolExecutor; nest_asyncio unavailable in this cell,
stdlib suffices — no nested loop needed). Cascade semantics ("rollback-able"):
every fix declares a `verify` gate; if verify FAILS, the fix is marked FAILED
and its `fallback` fix runs instead. All fixes are additive/forward-only —
"rollback" means graceful degradation to the next fix, never a revert.

Fix kinds:
  db   — executed by the agent via the daemon-native muse.db tool (Postgres,
         not script-reachable; the manifest carries the SQL, the agent runs it)
  job  — submitted to /home/toxic/fleet/jobs/bin/job on awrawr-pc (parallel-safe)
  cell — shell command in this cell (unshare-wrapped per standing directive)

Rounds are sequential (round N+1 reads round N's results); fixes within a
round are parallel. Results: rounds/results_R{n}.json
"""
import asyncio
import concurrent.futures
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "rounds_manifest.json")
RESULTS_DIR = os.path.join(HERE, "rounds")
os.makedirs(RESULTS_DIR, exist_ok=True)

UNSHARE = ["sudo", "unshare", "--mount", "--fork", "--propagation", "private"]
BRIDGE = [os.path.expanduser("~/workspace/skills/awrawr-mcp/bin/exec.py")]
JOB = ["/home/toxic/fleet/jobs/bin/job"]

POOL = concurrent.futures.ThreadPoolExecutor(max_workers=6)


def sh_cell(cmd: str, timeout: int = 120) -> tuple:
    """Run a cell command, always inside the root namespace."""
    try:
        p = subprocess.run(UNSHARE + ["bash", "-c", cmd],
                           capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-4000:]
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def sh_bridge(cmd: str, timeout: int = 120) -> tuple:
    """Run a command on awrawr-pc via the bridge, unshare-wrapped both ends."""
    try:
        p = subprocess.run(
            UNSHARE + [sys.executable, BRIDGE[0], cmd],
            capture_output=True, text=True, timeout=timeout,
            cwd=os.path.expanduser("~/workspace/skills/awrawr-mcp"))
        return p.returncode, (p.stdout + p.stderr)[-4000:]
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def job_submit(spec_path: str) -> tuple:
    rc, out = sh_bridge(f"{JOB[0]} submit {spec_path}", timeout=60)
    jid = out.strip().split("\n")[-1].strip() if rc == 0 else ""
    return rc, jid


def job_result(jid: str, timeout_s: int = 600) -> dict:
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
    return {"status": "timeout"}


async def run_fix(fix: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        loop = asyncio.get_event_loop()
        fid = fix["id"]
        t0 = time.time()
        rec = {"id": fid, "name": fix["name"], "kind": fix["kind"]}
        try:
            if fix["kind"] == "cell":
                rc, out = await loop.run_in_executor(
                    POOL, sh_cell, fix["run"], fix.get("timeout", 120))
                rec.update({"rc": rc, "out": out[-1500:]})
                ok = rc == 0
            elif fix["kind"] == "job":
                rc, jid = await loop.run_in_executor(POOL, job_submit, fix["spec"])
                rec["job_id"] = jid
                if rc != 0:
                    ok = False
                else:
                    jr = await loop.run_in_executor(POOL, job_result, jid,
                                                    fix.get("timeout", 600))
                    rec["job"] = jr
                    ok = jr["status"] == "done"
            elif fix["kind"] == "db":
                # Agent-executed: the manifest carries SQL; the agent runs it
                # via muse.db and records the outcome here.
                rec["sql"] = fix["run"]
                rec["note"] = "agent-executed via muse.db"
                ok = fix.get("agent_done", False)
            else:
                ok, rec["error"] = False, f"unknown kind {fix['kind']}"
            # verify gate
            if ok and fix.get("verify"):
                vkind = fix["verify"]["kind"]
                if vkind == "cell":
                    rc, out = await loop.run_in_executor(
                        POOL, sh_cell, fix["verify"]["run"], 60)
                    ok = rc == 0 and fix["verify"].get("expect", "") in out
                    rec["verify_out"] = out[-800:]
                elif vkind == "manual":
                    ok = fix["verify"].get("agent_confirmed", False)
            rec["verdict"] = "PASS" if ok else "FAIL"
            # cascade: on FAIL, run the fallback fix
            if not ok and fix.get("fallback"):
                rec["fallback_triggered"] = fix["fallback"]["id"]
                fb = await run_fix(fix["fallback"], sem)
                rec["fallback_result"] = fb
        except Exception as e:
            rec["verdict"] = "FAIL"
            rec["error"] = f"{type(e).__name__}: {e}"
        rec["elapsed_s"] = round(time.time() - t0, 1)
        return rec


async def run_round(n: int, manifest: dict) -> dict:
    rnd = manifest["rounds"][n - 1]
    sem = asyncio.Semaphore(3)
    fixes = [run_fix(f, sem) for f in rnd["fixes"]]
    results = await asyncio.gather(*fixes)
    summary = {"round": n, "title": rnd["title"],
               "fixes": results,
               "passes": sum(1 for r in results if r["verdict"] == "PASS"),
               "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    path = os.path.join(RESULTS_DIR, f"results_R{n}.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=1)
    return summary


def main(argv):
    with open(MANIFEST) as f:
        manifest = json.load(f)
    rounds = [int(x) for x in argv[1:]] or [1]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for n in rounds:
        summary = loop.run_until_complete(run_round(n, manifest))
        print(json.dumps(
            {"round": n, "passes": summary["passes"], "total": len(summary["fixes"]),
             "verdicts": [(r["id"], r["verdict"]) for r in summary["fixes"]]}, indent=1))


if __name__ == "__main__":
    main(sys.argv)
