#!/usr/bin/env python3
"""Storm burst analysis — 2026-09-16 extended 8-task run.

Uses the 48h ledger aggregates pulled via muse.db (ipython-style pandas
analysis) + subprocess for live host state. Stdlib + numpy + pandas only.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta

import numpy as np
import pandas as pd

CANONICAL_MD5 = "b4aefd29108f232f9c0d5a4b030215c1"
WINDOW_START = 1789362513  # 48h before ~2026-09-16T05:08Z
WINDOW_END = 1789535313

# Hourly refusal buckets from ledger: (hour_epoch, refused_n)
HOURLY = [
    (497047, 1),
    (497068, 5),
    (497070, 16),
    (497071, 3),
    (497091, 6),
    (497092, 8),
    (497093, 10),
]

# Duration stats from ledger (completed_at - created_at, seconds)
DUR = {
    "refused": {"n": 49, "min": 0, "avg": 2, "max": 6, "parents": 7},
    "genuine": {"n": 369, "min": 1, "avg": 838, "max": 10940, "parents": 29},
}

MDT = timezone(timedelta(hours=-6))


def h(epoch_hour: int) -> datetime:
    return datetime.fromtimestamp(epoch_hour * 3600, tz=timezone.utc)


def sh(*cmd: str) -> str:
    """subprocess helper: run, return stdout stripped; never raise."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return (r.stdout or "").strip()
    except Exception as e:  # noqa: BLE001
        return f"<err: {e}>"


def main() -> None:
    df = pd.DataFrame(HOURLY, columns=["hour_epoch", "refused_n"])
    df["hour_utc"] = df["hour_epoch"].apply(h)
    df["hour_mdt"] = df["hour_utc"].apply(lambda d: d.astimezone(MDT))
    df = df.sort_values("hour_epoch").reset_index(drop=True)

    # Inter-burst gaps (hours between burst starts)
    gaps = np.diff(df["hour_epoch"].to_numpy(dtype=float))

    total_refused = int(df["refused_n"].sum())
    total_spawns = 418
    refused_share = total_refused / total_spawns

    # Burstiness: coefficient of variation of hourly counts over the full
    # 48h window (zeros for the 41 quiet hours)
    full = np.zeros(48)
    base = int((WINDOW_START // 3600))
    for he, n in HOURLY:
        idx = int(he - base)
        if 0 <= idx < 48:
            full[idx] = n
    cv = float(full.std() / full.mean()) if full.mean() else 0.0

    # Refusal latency fingerprint
    r, g = DUR["refused"], DUR["genuine"]

    # Live host state via subprocess (ipython `!cmd` equivalent)
    poller_log_tail = sh("tail", "-n", "3", "/home/hatch/workspace/service-health.log")
    poller_procs = sh("bash", "-c", "ps -eo pid,etime,cmd | grep '[s]ervice-health-poller' | head -3")
    boot_id = sh("cat", "/proc/sys/kernel/random/boot_id").strip()
    stored_boot = sh("cat", "/home/hatch/.cell-boot-id").strip()

    report = {
        "window_utc": [h(base).isoformat(), h(base + 48).isoformat()],
        "total_spawns_48h": total_spawns,
        "refused_n": total_refused,
        "refused_share": round(refused_share, 4),
        "burst_hours": [
            {
                "utc": row.hour_utc.strftime("%m-%d %H:%M"),
                "mdt": row.hour_mdt.strftime("%m-%d %H:%M"),
                "n": int(row.refused_n),
            }
            for row in df.itertuples()
        ],
        "inter_burst_gaps_h": [round(float(x), 1) for x in gaps],
        "burstiness_cv_48h": round(cv, 2),
        "refusal_latency_s": {"avg": r["avg"], "max": r["max"], "distinct_parents": r["parents"]},
        "genuine_latency_s": {"avg": g["avg"], "max": g["max"], "distinct_parents": g["parents"]},
        "latency_separation_ratio": round(g["avg"] / max(r["avg"], 1), 1),
        "live": {
            "boot_id": boot_id,
            "stored_boot_id": stored_boot,
            "boot_changed": boot_id != stored_boot,
            "poller_procs": poller_procs,
            "poller_log_tail": poller_log_tail,
        },
    }

    out = "/home/hatch/workspace/refusal-hunt/storm-burst-report-20260916.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2)

    print(f"wrote {out}")
    print(f"refusals: {total_refused}/{total_spawns} ({refused_share:.1%})")
    print(f"burstiness CV (48h, zeros included): {cv:.2f}  (>1.0 = bursty)")
    print(f"inter-burst gaps (h): {[round(float(x),1) for x in gaps]}")
    print(f"refusal latency avg {r['avg']}s vs genuine avg {g['avg']}s "
          f"(~{g['avg']/max(r['avg'],1):.0f}x separation)")
    print(f"boot changed since stored: {boot_id != stored_boot}")
    print("poller procs:", poller_procs.splitlines()[0] if poller_procs else "<none>")
    for row in df.itertuples():
        print(f"  burst {row.hour_utc.strftime('%m-%d %H:%MZ')} "
              f"({row.hour_mdt.strftime('%m-%d %H:%M MDT')}): {int(row.refused_n)} refusals")


if __name__ == "__main__":
    sys.exit(main())
