#!/usr/bin/env python3
"""proc_delta.py -- proc-graph delta monitor (wave-8 task 5).

Snapshots the process table each run and diffs against an additive baseline.
Wake condition: a NEW PPID-0 daemon (PPid 0 in /proc/<pid>/status) not seen
in the baseline. PPID-0 PIDs are stable (PID 1, PID 67, ...), so any new one
is genuinely new root-level machinery, not PID churn.

State: ~/workspace/refusal-hunt/state/procs/
  baseline.json    {"ppid0": {pid: {"comm":..., "cmdline":...}}, "all": {...}}
  history.jsonl    append-only poll rows

Output: JSON {"ppid0_now": [...], "new_ppid0": [...], "n_procs": n, "ms": t}
exit 0 = no delta, exit 2 = new PPID-0 daemon(s).
"""
import json
import os
import time

STATE = os.path.expanduser("~/workspace/refusal-hunt/state/procs")


def snapshot():
    procs = {}
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        pid = int(p)
        try:
            with open(f"/proc/{p}/status") as f:
                txt = f.read()
            ppid = None
            for line in txt.splitlines():
                if line.startswith("PPid:"):
                    ppid = int(line.split()[1])
                    break
            comm = open(f"/proc/{p}/comm").read().strip()
        except Exception:
            continue
        try:
            with open(f"/proc/{p}/cmdline", "rb") as f:
                cmd = f.read().replace(b"\x00", b" ").decode(
                    "utf-8", "replace").strip()[:300]
        except Exception:
            cmd = ""
        procs[pid] = {"ppid": ppid, "comm": comm, "cmdline": cmd}
    return procs


def load_json(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def main():
    os.makedirs(STATE, exist_ok=True)
    t0 = time.monotonic()
    procs = snapshot()
    ppid0 = {str(pid): v for pid, v in procs.items() if v["ppid"] == 0}
    baseline = load_json(os.path.join(STATE, "baseline.json"), None)
    new = []
    if baseline is None:
        # Cold start: establish baseline silently, no wake.
        baseline = {"ppid0": ppid0,
                    "established": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                 time.gmtime())}
        with open(os.path.join(STATE, "baseline.json"), "w") as f:
            json.dump(baseline, f, indent=1)
        cold = True
    else:
        cold = False
        known = set(baseline.get("ppid0", {}))
        new = sorted(int(pid) for pid in ppid0 if pid not in known)
    ms = int((time.monotonic() - t0) * 1000)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "n_procs": len(procs), "ppid0_count": len(ppid0),
           "ppid0_pids": sorted(int(p) for p in ppid0),
           "new_ppid0": new, "cold_start": cold, "ms": ms}
    with open(os.path.join(STATE, "history.jsonl"), "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps({**rec,
                      "new_ppid0_detail": {str(p): ppid0[str(p)] for p in new}}))
    return 2 if new else 0


if __name__ == "__main__":
    raise SystemExit(main())
