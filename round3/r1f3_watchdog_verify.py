#!/usr/bin/env python3
"""R1F3 gate-clear-watch existence check + watchdog verify.
Checks: (1) gate-clear-watch cron definition exists and is enabled,
(2) sorry-watchdog daemon alive on awrawr-pc, (3) LATEST.json readable
with a storm_active boolean. Prints PASS/FAIL with reasons."""
import json, re, sys, time
sys.path.insert(0, "/home/hatch/workspace/refusal-hunt/round3")
import round_runner as rr

def main():
    fails = []
    # 1. cron definition
    cron_md = "/home/hatch/workspace/goals/safety-review-gate-investigation/crons/minutely/gate-clear-watch__interval@15m.md"
    try:
        head = open(cron_md).read(2000)
        m = re.search(r"^enabled:\s*(\S+)", head, re.M)
        if not m or m.group(1).lower() != "true":
            fails.append("gate-clear-watch cron not enabled")
    except FileNotFoundError:
        fails.append("gate-clear-watch cron definition missing")
    # 2. watchdog daemon on awrawr-pc
    rc, out = rr.sh_bridge("pgrep -f 'sorry-watchdog\\.py' | head -3")
    if rc != 0 or not out.strip():
        fails.append("sorry-watchdog daemon not running on awrawr-pc")
    # 3. LATEST.json readable + storm_active present + recent
    try:
        d = json.load(open("/home/hatch/workspace/refusal-hunt/sorry-audit/LATEST.json"))
        if not isinstance(d.get("storm_active"), bool):
            fails.append("LATEST.json storm_active not boolean")
        ga = d.get("generated_at")
        if isinstance(ga, (int, float)) and (time.time() - ga) > 3600:
            fails.append("LATEST.json stale >1h")
    except Exception as e:
        fails.append(f"LATEST.json unreadable: {e}")
    if fails:
        print("FAIL")
        for f in fails: print(" ", f)
        return 1
    print("PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
