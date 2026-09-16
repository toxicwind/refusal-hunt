#!/usr/bin/env python3
"""Lane 7: commit+push daemon repairs, surgical per-file adds only.
Repairs and their repos (verified 2026-09-16):
  squawk feed      -> /home/toxic/squawk            (restored fleet_*.py, agent_chat/*)
  paper-poller     -> /home/toxic/paper-poller      (.git gutted: no HEAD; report only)
  boundless        -> /home/toxic/boundless/.venv    (venv recreate; repo files untouched?)
  itvx-browserless -> /home/toxic/.browserless       (node_modules + external/*.js; likely not a repo)
Never sweeps unrelated working-tree state: `git add` only the repaired paths."""
import json, os, subprocess

REPAIRS = [
    {"name": "squawk-feed", "repo": "/home/toxic/squawk",
     "paths": ["fleet_relay.py", "fleet_ws.py", "agent_chat"],
     "msg": "repair: restore squawk-feed source modules wiped by shared-checkout fratricide (verified live :25135)"},
    {"name": "boundless", "repo": "/home/toxic/boundless",
     "paths": [],  # venv is gitignored; commit only if repo files changed
     "msg": "repair: recreate boundless venv (uvicorn+fastapi+ebooklib); verified live :10200"},
    {"name": "itvx-browserless", "repo": "/home/toxic/.browserless",
     "paths": ["app/external/browser.js", "app/external/page.js"],
     "msg": "repair: restore itvx hook stubs + npm ci (index.mjs, puppeteer-core.js); verified live :25130"},
    {"name": "paper-poller", "repo": "/home/toxic/paper-poller",
     "paths": ["bin/poller.py", "bin/watchdog.py", "bin/race_papers.py"],
     "msg": "repair: restore poller.py/watchdog.py/race_papers.py from deep-paper-reader copy; verified live :25149"},
]

def sh(args, cwd, timeout=60):
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()[:2000]
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"

def main():
    report = []
    for r in REPAIRS:
        repo = r["repo"]
        entry = {"repair": r["name"], "repo": repo}
        rc, out = sh(["git", "rev-parse", "--show-toplevel"], repo)
        if rc != 0:
            entry["git"] = "not-a-repo"
            entry["detail"] = out[:200]
            report.append(entry)
            continue
        toplevel = out.split("\n")[0]
        entry["toplevel"] = toplevel
        rc, status = sh(["git", "status", "--short"], toplevel)
        entry["status_before"] = status[:800]
        added = []
        for p in r["paths"]:
            full = os.path.join(toplevel, p)
            if os.path.exists(full):
                rc, _ = sh(["git", "add", p], toplevel)
                if rc == 0:
                    added.append(p)
        entry["added"] = added
        if added:
            rc, diff = sh(["git", "diff", "--cached", "--stat"], toplevel)
            entry["staged_stat"] = diff[:400]
            rc, cm = sh(["git", "commit", "-m", r["msg"]], toplevel)
            entry["commit_rc"] = rc
            entry["commit_out"] = cm[:300]
            if rc == 0:
                rc, ps = sh(["git", "push"], toplevel, timeout=120)
                entry["push_rc"] = rc
                entry["push_out"] = ps[:300]
        else:
            entry["note"] = "no repairable tracked paths changed; nothing staged"
        report.append(entry)
    print(json.dumps(report, indent=1))

if __name__ == "__main__":
    main()
