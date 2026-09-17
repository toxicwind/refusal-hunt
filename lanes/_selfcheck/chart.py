"""Findings charts: spawn refusal-rate escalation + storm-row hour histogram."""
import os
OUT = os.path.expanduser("~/workspace/refusal-hunt/lanes/_selfcheck")
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception as e:
    print("matplotlib unavailable:", e)
    raise SystemExit

import pyarrow.parquet as pq
import pandas as pd

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

days = ["09-14", "09-15", "09-16", "09-17*"]
n = [242, 124, 396, 10]
ref = [1, 24, 87, 9]
rate = [100 * r / t for r, t in zip(ref, n)]
bars = ax1.bar(days, rate, color=["#4caf50", "#ff9800", "#f44336", "#b71c1c"])
ax1.set_title("Spawn refusal share by day (status=completed, md5=spawn-storm)")
ax1.set_ylabel("% refused")
for b, v, t, r in zip(bars, rate, n, ref):
    ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 1, f"{v:.1f}%\n({r}/{t})",
             ha="center", va="bottom", fontsize=9)
ax1.set_ylim(0, 110)

t = pq.read_table(os.path.expanduser("~/workspace/refusal-hunt/ledger/anomalies.parquet")).to_pandas()
t["created_at"] = pd.to_datetime(t["created_at"], format="mixed", utc=True)
t["hour"] = t["created_at"].dt.hour
hc = t["hour"].value_counts().sort_index()
ax2.bar(hc.index, hc.values, color="#5c6bc0")
ax2.set_title("Storm rows by hour (UTC)")
ax2.set_xlabel("hour UTC")
ax2.set_ylabel("rows")

fig.suptitle("Refusal-storm forensics 2026-09-17 — direct-lane results after 8/8 spawn refusals")
fig.tight_layout()
fp = os.path.join(OUT, "storm_findings.png")
fig.savefig(fp, dpi=110)
print("wrote", fp, os.path.getsize(fp), "bytes")
