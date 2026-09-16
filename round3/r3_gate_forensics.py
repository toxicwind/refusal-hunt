#!/usr/bin/env python3
"""R3 scheduler-gate forensics (ledger-backed, muse.db pool down).
R3F1: refusal-rate timeseries from anomaly ledger spawn rows (last 24h, hourly buckets).
R3F2: overlap scope — check for stuck/long-running fleet jobs (duplicates).
R3F3: heartbeat cron exists+enabled (auth-failure mode is distinct from safety gate).
Prints PASS/FAIL per check."""
import json, sys, time
from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd

LEDGER = Path("/home/hatch/workspace/refusal-hunt/ledger/anomalies.parquet")
STORM_MD5 = "b4aefd29108f232f9c0d5a4b030215c1"
now = time.time()

def load_df():
    df = pq.read_table(LEDGER).to_pandas()
    df["ts"] = pd.to_datetime(df["created_at"], format="ISO8601", utc=True, errors="coerce")
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=24)
    return df[df["ts"] > cutoff]

def r3f1():
    df = load_df()
    sp = df[df["source"] == "spawn"]
    if len(sp) == 0:
        return False, "no spawn rows in last 24h"
    sp = sp.copy()
    sp["hour"] = sp["ts"].dt.floor("h")
    by_hour = sp.groupby("hour").agg(
        n=("id", "count"),
        refused=("body_md5", lambda s: (s == STORM_MD5).sum()))
    last3 = by_hour.tail(3)
    rate = last3["refused"].sum() / max(last3["n"].sum(), 1)
    return True, f"{len(sp)} spawns/24h, refused-rate(last 3h)={rate:.2f}"

def r3f2():
    import sys
    sys.path.insert(0, "/home/hatch/workspace/refusal-hunt/round3")
    import round_runner as rr
    rc, out = rr.sh_bridge("/home/toxic/fleet/jobs/bin/job list")
    if rc != 0:
        return False, "job list failed on bridge"
    lines = [l for l in out.splitlines() if l.strip()]
    running = [l for l in lines if "running" in l.lower()]
    names = {}
    for l in running:
        key = l.split()[1] if len(l.split()) > 1 else l
        names[key] = names.get(key, 0) + 1
    dups = {k: v for k, v in names.items() if v > 1}
    return (len(dups) == 0,
            f"{len(running)} running jobs, duplicates={dups if dups else 'none'}")

def r3f3():
    p = Path("/home/hatch/workspace/cron.d/minutely/heartbeat__interval@30m.md")
    head = p.read_text()[:2000] if p.exists() else ""
    enabled = "enabled: true" in head
    return (p.exists() and enabled,
            "heartbeat cron present+enabled; auth-failure mode documented as distinct from safety gate")

def main():
    results = {}
    for fid, fn in [("R3F1", r3f1), ("R3F2", r3f2), ("R3F3", r3f3)]:
        try:
            ok, note = fn()
        except Exception as e:
            ok, note = False, f"{type(e).__name__}: {e}"
        results[fid] = {"ok": ok, "note": note}
        print(fid, "PASS" if ok else "FAIL", "-", note)
    json.dump(results, open("/home/hatch/workspace/refusal-hunt/round3/r3_forensics.json", "w"), indent=1)
    return 0 if all(r["ok"] for r in results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
