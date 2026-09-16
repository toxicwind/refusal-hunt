#!/usr/bin/env python3
"""spawn_hook.py — the ONE consistent way to launch durable tasks.

Problem it fixes: ad-hoc subagent.spawn calls abort opaquely (no id, no
ledger row, no tracking). This hook routes every durable launch through the
bridge's first-class agent path (awrawr-mcp bin/agent.py -> fleet job runner
on awrawr-pc: detached setsid, survives cell death, queryable, C2-tracked),
with pre-flight checks, echo-dedupe, and result tracking in one JSONL ledger.

Usage:
  spawn_hook.py launch --name NAME [--tag TAG] [--cwd DIR] [--timeout S] -- <cmd...>
  spawn_hook.py wait   <jobid> [--timeout S]
  spawn_hook.py result <jobid> [--tail N]
  spawn_hook.py audit

Every launch records: timestamp, launcher, internal tool invoked, task hash,
job id, terminal state, result digest. No fixed sleeps: wait() polls the real
job state with short bounded checks.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

SKILL_BIN = os.path.expanduser("~/workspace/skills/awrawr-mcp/bin")
EXEC_PY = os.path.join(SKILL_BIN, "exec.py")
AGENT_PY = os.path.join(SKILL_BIN, "agent.py")
LEDGER = os.path.expanduser("~/workspace/c2/hook-launches.jsonl")
DEDUP_WINDOW_S = 24 * 3600
POLL_INTERVAL_S = 3


def run(cmd, timeout=60):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def ledger_append(rec):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def task_hash(name, cmd, cwd):
    h = hashlib.sha256()
    h.update(json.dumps({"name": name, "cmd": cmd, "cwd": cwd},
                        sort_keys=True).encode())
    return h.hexdigest()[:16]


def recent_duplicate(thash):
    """Echo protection: same task hash with terminal success in window."""
    if not os.path.exists(LEDGER):
        return None
    now = time.time()
    try:
        with open(LEDGER) as f:
            lines = f.readlines()
    except OSError:
        return None
    for line in reversed(lines[-200:]):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("task_hash") != thash:
            continue
        try:
            ts = time.mktime(time.strptime(r["ts"], "%Y-%m-%dT%H:%M:%SZ"))
        except (KeyError, ValueError):
            continue
        if now - ts < DEDUP_WINDOW_S and r.get("terminal_state") == "done":
            return r
    return None


def bridge_alive():
    rc, out, err = run([sys.executable, EXEC_PY, "--argv",
                        "echo", "hook-ok"], timeout=60)
    return rc == 0 and "hook-ok" in out, out or err


def parse_job_id(out):
    """Defensive: try JSON first, then common id patterns."""
    try:
        d = json.loads(out)
        for k in ("job_id", "id", "jid"):
            if k in d:
                return str(d[k])
    except (json.JSONDecodeError, TypeError):
        pass
    import re
    m = re.search(r"(job[_-]?id\s*[:=]\s*)([A-Za-z0-9_.-]+)", out,
                  re.IGNORECASE)
    if m:
        return m.group(2)
    m = re.search(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
                  r"[0-9a-f]{4}-[0-9a-f]{12})\b", out)
    if m:
        return m.group(1)
    # fleet job ids are bare tokens: YYYYMMDD-HHMMSS-xxxx on their own line
    m = re.search(r"(?m)^\s*(\d{8}-\d{6}-[0-9a-f]{4})\s*$", out)
    if m:
        return m.group(1)
    return None


def preflight_sanitize(name, cmd):
    """Wave-8: pre-classifier gate on the launch path (additive, fail-open).

    Runs sanitize_job_body on the task text before it is submitted, so
    refusal-shaped or trigger-dense bodies never ride into a launch.
    Returns (blocked: bool, report: dict). Any internal error -> not blocked,
    never breaks a launch (fail-open; the ledger still records it).
    """
    try:
        bindir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "bin")
        if bindir not in sys.path:
            sys.path.insert(0, bindir)
        import sanitize_job_body
        cleaned, report = sanitize_job_body.sanitize(
            ns_name_cmd(name, cmd))
        return bool(report.get("quarantined")), report
    except Exception as e:  # fail-open: a broken gate must not kill launches
        return False, {"gate_error": f"{type(e).__name__}: {e}"[:120]}


def ns_name_cmd(name, cmd):
    return name + "\n" + " ".join(cmd)


def postflight_check(out):
    """Wave-8: banned-token gate on the launch RESULT (additive, fail-open).

    Returns (hit: bool, hits: list). Ledger records the digest, never bodies.
    """
    try:
        bindir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "bin")
        if bindir not in sys.path:
            sys.path.insert(0, bindir)
        import banned_token_check
        hits = banned_token_check.check(out or "")
        return bool(hits), hits
    except Exception as e:
        return False, [f"gate_error:{type(e).__name__}"]


def cmd_launch(args):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--tag", default="")
    ap.add_argument("--cwd", default="/home/toxic")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    ns = ap.parse_args(args)
    cmd = [c for c in ns.cmd if c != "--"]
    if not cmd:
        print("launch: no command given", file=sys.stderr)
        return 2

    thash = task_hash(ns.name, cmd, ns.cwd)

    # Wave-8 pre-flight: sanitize the task body before it reaches any
    # classifier-adjacent path. Quarantined bodies are refused locally with
    # a ledger event (no launch attempted, nothing deleted).
    blocked, pf_report = preflight_sanitize(ns.name, cmd)
    if blocked:
        ledger_append({"event": "launch_refused_preflight",
                       "name": ns.name, "tag": ns.tag,
                       "task_hash": thash, "cmd": cmd, "cwd": ns.cwd,
                       "preflight": pf_report})
        print(json.dumps({"ok": False, "reason": "preflight_quarantine",
                          "preflight": pf_report}))
        return 1

    dup = recent_duplicate(thash)
    if dup:
        print(json.dumps({"ok": False, "reason": "duplicate",
                          "prior": dup}))
        return 0

    ok, info = bridge_alive()
    rec = ledger_append({"event": "launch_attempt", "name": ns.name,
                         "tag": ns.tag, "task_hash": thash,
                         "tool": "awrawr-mcp/bin/agent.py submit",
                         "cmd": cmd, "cwd": ns.cwd,
                         "bridge_ok": ok, "bridge_info": info[:200]})
    if not ok:
        print(json.dumps({"ok": False, "reason": "bridge_down",
                          "detail": info[:300]}))
        return 1

    rc, out, err = run([sys.executable, AGENT_PY, "submit",
                        "--name", ns.name, "--"] + cmd, timeout=120)
    jid = parse_job_id(out)
    rec.update({"event": "launched", "job_id": jid,
                "rc": rc, "stdout_tail": out[-300:],
                "stderr_tail": err[-300:]})
    ledger_append(rec)
    print(json.dumps({"ok": bool(jid), "job_id": jid,
                      "task_hash": thash, "rc": rc,
                      "raw": (out + "\n" + err)[-500:]}))
    return 0 if jid else 1


def job_state(jid):
    rc, out, err = run([sys.executable, AGENT_PY, "status", jid],
                       timeout=60)
    blob = (out + "\n" + err).lower()
    for state in ("done", "failed", "killed", "errored", "dead"):
        if state in blob:
            return state, out
    if "running" in blob or "pending" in blob or "active" in blob:
        return "running", out
    return "unknown", out or err


def cmd_wait(args):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("jobid")
    ap.add_argument("--timeout", type=int, default=600)
    ns = ap.parse_args(args)
    deadline = time.time() + ns.timeout
    last = "unknown"
    # Bounded condition polling: check the real job state, never sleep blind.
    while time.time() < deadline:
        state, _ = job_state(ns.jobid)
        last = state
        if state in ("done", "failed", "killed", "errored", "dead"):
            break
        time.sleep(POLL_INTERVAL_S)
    ledger_append({"event": "wait_finished", "job_id": ns.jobid,
                   "terminal_state": last})
    print(json.dumps({"job_id": ns.jobid, "terminal_state": last}))
    return 0


def cmd_result(args):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("jobid")
    ap.add_argument("--tail", type=int, default=40)
    ns = ap.parse_args(args)
    rc, out, err = run([sys.executable, AGENT_PY, "result", ns.jobid],
                       timeout=60)
    digest = hashlib.md5(out.encode()).hexdigest()
    # Wave-8 post-flight: banned-token gate on the result body. The ledger
    # records the digest only (loop-fuel rule: never store refusal bodies).
    banned, banned_hits = postflight_check(out)
    rec = {"event": "result_fetched", "job_id": ns.jobid,
           "result_md5": digest, "result_len": len(out),
           "banned_token_hit": banned}
    if banned:
        rec["banned_hits"] = banned_hits
    ledger_append(rec)
    print(out[-4000:])
    print(json.dumps({"job_id": ns.jobid, "md5": digest,
                      "len": len(out)}), file=sys.stderr)
    return 0


def cmd_audit(_args):
    rc, out, err = run([sys.executable, AGENT_PY, "roster"], timeout=60)
    n_ledger = 0
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            n_ledger = sum(1 for _ in f)
    print(json.dumps({"roster_rc": rc,
                      "roster_tail": out[-1500:],
                      "ledger_lines": n_ledger,
                      "ledger": LEDGER}))
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    verb, rest = sys.argv[1], sys.argv[2:]
    return {"launch": cmd_launch, "wait": cmd_wait,
            "result": cmd_result, "audit": cmd_audit}.get(
                verb, lambda a: (print("unknown verb", verb), 2))(rest)


if __name__ == "__main__":
    sys.exit(main())
