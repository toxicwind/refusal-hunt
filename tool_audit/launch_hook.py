#!/usr/bin/env python3
"""launch_hook.py — auditable task launcher.

Every task launch is ledgered (timestamp, spec hash, dispatch path, outcome,
latency) so "starting tools/tasks is BROKEN" becomes data instead of vibes.

Dispatch paths:
  local  — subprocess on this machine, hard timeout, captured output
  fleet  — /home/toxic/fleet/jobs/bin/job submit -- <cmd> on awrawr-pc via bridge

Refusal signatures in output are detected (md5 identity, never plaintext) and
logged per the refusal directive.

Usage:
  launch_hook.py submit --via fleet --name NAME -- CMD [ARGS...]
  launch_hook.py submit --via local --name NAME --timeout 60 -- CMD [ARGS...]
  launch_hook.py selftest
  launch_hook.py ledger [--tail N]
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

BASE = os.path.expanduser("~/workspace/refusal-hunt/tool_audit")
LEDGER = os.path.join(BASE, "launches.jsonl")
BRIDGE = os.path.expanduser("~/workspace/skills/awrawr-mcp/bin/exec.py")
JOB_BIN = "/home/toxic/fleet/jobs/bin/job"

# md5 identities of known canned-refusal bodies (never store plaintext)
REFUSAL_MD5 = {
    "b4aefd29108f232f9c0d5a4b030215c1": "spawn-level 384-char canned refusal",
    "582bcbd080daeb3f826c45ed4a83b265": "chat-level 96-char canned refusal",
}
# short distinctive substrings observed in refused helper outputs (not the refusal itself)
REFUSAL_MARKERS = [
    "safety policy refused this helper's work",
    "do not retry it, rephrase it, or route around it",
]


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def log_launch(record):
    os.makedirs(BASE, exist_ok=True)
    record["ts"] = utcnow()
    with open(LEDGER, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def detect_refusal(output):
    h = hashlib.md5(output.strip().encode()).hexdigest()
    if h in REFUSAL_MD5:
        return {"hit": True, "kind": REFUSAL_MD5[h], "via": "md5"}
    for m in REFUSAL_MARKERS:
        if m in output:
            return {"hit": True, "kind": "refusal-marker-substring", "via": "marker"}
    return {"hit": False}


def run_local(cmd, timeout):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + (p.stderr or "")
        return {"ok": p.returncode == 0, "rc": p.returncode,
                "latency_ms": int((time.time() - t0) * 1000),
                "output_tail": out[-2000:], "refusal": detect_refusal(out)}
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or b"").decode(errors="replace")
               + (e.stderr or b"").decode(errors="replace"))
        return {"ok": False, "rc": "timeout", "latency_ms": int((time.time() - t0) * 1000),
                "output_tail": out[-2000:], "refusal": detect_refusal(out)}


def run_fleet(cmd, timeout):
    # submit then poll status until terminal; condition-polled, short inter-check gaps
    t0 = time.time()
    sub = subprocess.run(
        [sys.executable, BRIDGE, "--timeout", "25", JOB_BIN + " submit -- " + " ".join(cmd)],
        capture_output=True, text=True, timeout=40)
    if sub.returncode != 0:
        return {"ok": False, "rc": "submit-failed",
                "latency_ms": int((time.time() - t0) * 1000),
                "output_tail": (sub.stdout + sub.stderr)[-2000:],
                "refusal": detect_refusal(sub.stdout + sub.stderr)}
    job_id = (sub.stdout or "").strip().split()[-1]
    deadline = t0 + timeout
    job_status, job_out = "submitted", ""
    while time.time() < deadline:
        st = subprocess.run(
            [sys.executable, BRIDGE, "--timeout", "20", JOB_BIN + " status " + job_id],
            capture_output=True, text=True, timeout=30)
        job_status = "unknown"
        for ln in (st.stdout or "").splitlines():
            if ln.strip().startswith("status:"):
                job_status = ln.split("status:")[1].strip()
                break
        if job_status in ("done", "failed", "timeout", "killed"):
            lg = subprocess.run(
                [sys.executable, BRIDGE, "--timeout", "20", JOB_BIN + " log " + job_id],
                capture_output=True, text=True, timeout=30)
            job_out = (lg.stdout or "") + (lg.stderr or "")
            break
        time.sleep(3)  # inter-poll gap; the condition (job terminal state) is what we wait on
    ok = job_status == "done"
    return {"ok": ok, "rc": job_status,
            "latency_ms": int((time.time() - t0) * 1000),
            "output_tail": job_out[-2000:], "refusal": detect_refusal(job_out),
            "job_id": job_id}


def cmd_submit(args):
    spec = {"name": args.name, "via": args.via, "cmd": args.cmd, "timeout": args.timeout}
    spec_sha = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:16]
    rec = log_launch({"event": "launch_attempt", "spec_sha": spec_sha, **spec})
    if args.via == "fleet":
        res = run_fleet(args.cmd, args.timeout)
    else:
        res = run_local(args.cmd, args.timeout)
    rec.update({"event": "launch_result", "spec_sha": spec_sha, **res})
    log_launch(rec)
    print(json.dumps({"spec_sha": spec_sha, "ok": res["ok"], "rc": res.get("rc"),
                      "latency_ms": res["latency_ms"],
                      "refusal_hit": res["refusal"]["hit"]}, indent=1))
    return 0 if res["ok"] else 1


def cmd_selftest(_args):
    print("== launch_hook selftest ==")
    r1 = run_local(["echo", "hook-alive"], 10)
    print("local echo:", "PASS" if (r1["ok"] and "hook-alive" in r1["output_tail"]) else "FAIL", r1)
    log_launch({"event": "selftest", "path": "local", **r1})
    r2 = run_fleet(["true"], 60)
    print("fleet true:", "PASS" if r2["ok"] else "FAIL", {k: r2.get(k) for k in ("rc", "job_id", "latency_ms")})
    log_launch({"event": "selftest", "path": "fleet", **{k: v for k, v in r2.items() if k != "output_tail"}})
    ok = r1["ok"] and r2["ok"]
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def cmd_ledger(args):
    if not os.path.exists(LEDGER):
        print("ledger empty")
        return 0
    with open(LEDGER) as f:
        lines = f.readlines()
    for ln in lines[-args.tail:]:
        print(ln.rstrip())
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="c", required=True)
    s = sub.add_parser("submit")
    s.add_argument("--via", choices=["local", "fleet"], required=True)
    s.add_argument("--name", required=True)
    s.add_argument("--timeout", type=int, default=120)
    s.add_argument("cmd", nargs=argparse.REMAINDER)
    s.set_defaults(f=cmd_submit)
    t = sub.add_parser("selftest")
    t.set_defaults(f=cmd_selftest)
    lg = sub.add_parser("ledger")
    lg.add_argument("--tail", type=int, default=10)
    lg.set_defaults(f=cmd_ledger)
    args = ap.parse_args()
    if getattr(args, "c", None) == "submit" and args.cmd and args.cmd[0] == "--":
        args.cmd = args.cmd[1:]
    sys.exit(args.f(args))


if __name__ == "__main__":
    main()
