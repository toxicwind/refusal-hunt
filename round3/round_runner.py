#!/usr/bin/env python3
"""round_runner.py — recursive 8-round refusal-storm repair orchestrator.

Each round = 3 fixes, ordered by confidence. Fixes run in PARALLEL within a
round (asyncio + ThreadPoolExecutor; poll-await style — no time.sleep,
no sleep/timeout binaries; bounded waits via asyncio.wait_for try/catch). Cascade semantics ("rollback-able"):
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
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "rounds_manifest.json")
RESULTS_DIR = os.path.join(HERE, "rounds")
os.makedirs(RESULTS_DIR, exist_ok=True)

UNSHARE_BASE = ["unshare", "--mount", "--fork", "--propagation", "private"]
# taskhook launches as root (uid 0); there sudo is unnecessary and its
# audit plugin breaks inside some namespaces ("unable to open
# /etc/sudoers: Invalid argument"). Skip sudo when already root.
UNSHARE = (UNSHARE_BASE if os.geteuid() == 0 else ["sudo"] + UNSHARE_BASE)
BRIDGE = [os.path.expanduser("~/workspace/skills/awrawr-mcp/bin/exec.py")]
JOB = ["/home/toxic/fleet/jobs/bin/job"]

POOL = concurrent.futures.ThreadPoolExecutor(max_workers=6)


def sh_cell(cmd: str, timeout: int = 120) -> tuple:
    """Run a cell command, always inside the root namespace.

    NOTE 2026-09-16: sudo sets HOME=/root inside the namespace, which broke
    every manifest path using ~ (writes went to /root/workspace). Export
    HOME explicitly so ~ resolves to the cell home.
    """
    cmd = "export HOME=/home/hatch; " + cmd
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


# Fleet job IDs look like 20260916-060508-cd4e. The bridge sometimes prefixes
# the submit output (e.g. "[exit=0] <jid>"), so extract by pattern instead of
# trusting the last line.
JOB_ID_RE = re.compile(r"\b(\d{8}-\d{6}-[0-9a-f]{4})\b")


def job_submit(spec_path: str) -> tuple:
    rc, out = sh_bridge(f"{JOB[0]} submit {spec_path}", timeout=60)
    m = JOB_ID_RE.search(out or "")
    jid = m.group(1) if (rc == 0 and m) else ""
    return rc, jid


def _job_result_legacy_blocking(jid: str, timeout_s: int = 600) -> dict:
    """DEPRECATED 2026-09-16: used time.sleep(5) blocking loop.

    Banned by standing order (no sleep/timeout binaries, no blocking
    sleeps). Kept for provenance only -- never call. Use job_result_async.
    """
    raise RuntimeError("legacy blocking poller is banned; use job_result_async")


async def job_result_async(jid: str, timeout_s: int = 600) -> dict:
    """Poll-await a fleet job: NO backoff, NO sleep anywhere.

    Per standing order 2026-09-16: sleep/timeout binaries are banned and
    even asyncio.sleep intervals are banned — poll-await style with
    try/catch timeouts. Each loop iteration is: poll status via the bridge
    (itself a bounded blocking round-trip, which paces the loop
    naturally), branch on the observed state, or loop again immediately.
    The outer deadline is enforced by comparing loop.time() each
    iteration; every bridge round-trip is wrapped in asyncio.wait_for
    (try/catch timeout). No sleep of any kind on the hot path.
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
            # terminal: result collection gets its own hard timeout
            try:
                rc2, res = await asyncio.wait_for(
                    loop.run_in_executor(
                        POOL, sh_bridge, f"{JOB[0]} result {jid}", 120),
                    timeout=125)
            except asyncio.TimeoutError:
                return {"status": "result-timeout"}
            if rc2 == 0:
                return {"status": "done", "result": res}
            return {"status": "result-error", "rc": rc2, "result": res}
        if "status:     failed" in out:
            try:
                rc2, log = await asyncio.wait_for(
                    loop.run_in_executor(
                        POOL, sh_bridge, f"{JOB[0]} log {jid}", 120),
                    timeout=125)
            except asyncio.TimeoutError:
                return {"status": "log-timeout"}
            return {"status": "failed", "log": (log or "")[-2000:]}
        # no backoff, no sleep: the blocking bridge round-trip inside the
        # awaited executor call is the loop's only pacing; each iteration
        # polls status again immediately after the await resolves.


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
            elif fix["kind"] == "bridge":
                rc, out = await loop.run_in_executor(
                    POOL, sh_bridge, fix["run"], fix.get("timeout", 120))
                rec.update({"rc": rc, "out": out[-1500:]})
                ok = rc == 0
            elif fix["kind"] == "job":
                rc, jid = await loop.run_in_executor(POOL, job_submit, fix["spec"])
                rec["job_id"] = jid
                if rc != 0:
                    ok = False
                else:
                    jr = await job_result_async(jid, fix.get("timeout", 600))
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
                elif vkind == "bridge":
                    rc, out = await loop.run_in_executor(
                        POOL, sh_bridge, fix["verify"]["run"], 60)
                    ok = rc == 0 and fix["verify"].get("expect", "") in out
                    rec["verify_out"] = out[-800:]
                elif vkind == "manual":
                    ok = fix["verify"].get("agent_confirmed", False)
            rec["verdict"] = "PASS" if ok else "FAIL"
            # Preserve manifest-authored outcome notes (e.g. R1F2's
            # REDIRECTED rationale) on the record alongside the real verdict.
            if isinstance(fix.get("result"), str):
                rec["note"] = fix["result"][:500]
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
    manifest_path = MANIFEST
    rest = []
    for a in argv[1:]:
        if a.startswith("--manifest="):
            manifest_path = a.split("=", 1)[1]
        else:
            rest.append(a)
    with open(manifest_path) as f:
        manifest = json.load(f)
    rounds = [int(x) for x in rest] or [1]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for n in rounds:
        summary = loop.run_until_complete(run_round(n, manifest))
        print(json.dumps(
            {"round": n, "passes": summary["passes"], "total": len(summary["fixes"]),
             "verdicts": [(r["id"], r["verdict"]) for r in summary["fixes"]]}, indent=1))


if __name__ == "__main__":
    main(sys.argv)
