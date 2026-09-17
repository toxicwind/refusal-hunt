"""Refusal-storm findings chart v2. Reads the anomalies ledger and produces a 2x2 figure.

Panel 1: storm rows per hour (UTC), stacked by source (chat / spawn / runtime.messages)
Panel 2: cumulative count of spawn-storm digest rows over time
Panel 3: per-day spawn refusal share (measured values)
Panel 4: histogram of body_len on log x-axis, storm digests vs all other rows
"""
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

LEDGER = "/home/hatch/workspace/refusal-hunt/ledger/anomalies.parquet"
OUT = "/home/hatch/workspace/refusal-hunt/lanes/_selfcheck/storm_findings_v2.png"

CHAT_DIGEST = "582bcbd080daeb3f826c45ed4a83b265"   # 96-char chat body
SPAWN_DIGEST = "b4aefd29108f232f9c0d5a4b030215c1"  # 384-char spawn body
STORM_DIGESTS = {CHAT_DIGEST, SPAWN_DIGEST}

df = pq.read_table(LEDGER).to_pandas()
df["created_at"] = pd.to_datetime(df["created_at"], utc=True, format="ISO8601")
df = df.sort_values("created_at").reset_index(drop=True)
storm = df[df["body_md5"].isin(STORM_DIGESTS)].copy()

fig, axes = plt.subplots(2, 2, figsize=(13, 9))
fig.suptitle("Refusal-storm findings (ledger: anomalies.parquet)", fontsize=14, fontweight="bold")

# --- Panel 1: storm rows per hour UTC, stacked by source ---
ax = axes[0, 0]
hour = storm["created_at"].dt.floor("h")
sources = ["chat", "spawn", "runtime.messages"]
pivot = pd.crosstab(hour, storm["source"])
for s in sources:
    if s not in pivot.columns:
        pivot[s] = 0
pivot = pivot[sources]
colors = {"chat": "#1f77b4", "spawn": "#d62728", "runtime.messages": "#9467bd"}
bottom = np.zeros(len(pivot))
for s in sources:
    ax.bar(pivot.index, pivot[s], bottom=bottom, width=0.035, label=s, color=colors[s])
    bottom += pivot[s].values
ax.set_title("(1) Storm rows per hour (UTC), stacked by source")
ax.set_xlabel("Hour (UTC)")
ax.set_ylabel("Rows")
ax.legend(fontsize=8)
fig.autofmt_xdate(rotation=30)
ax.tick_params(axis="x", labelsize=7)

# --- Panel 2: cumulative spawn-storm digest rows ---
ax = axes[0, 1]
spawn_storm = storm[storm["body_md5"] == SPAWN_DIGEST].sort_values("created_at")
cum = np.arange(1, len(spawn_storm) + 1)
ax.step(spawn_storm["created_at"], cum, where="post", color="#d62728", linewidth=2)
ax.set_title("(2) Cumulative spawn-storm digest rows")
ax.set_xlabel("Time (UTC)")
ax.set_ylabel("Cumulative rows")
ax.tick_params(axis="x", labelsize=7)
ax.grid(alpha=0.3)

# --- Panel 3: per-day spawn refusal share (measured values) ---
ax = axes[1, 0]
# a row counts as refused when md5(final_response) == 384-char digest
measured = [
    ("2026-09-14", 1, 242),
    ("2026-09-15", 24, 124),
    ("2026-09-16", 87, 396),
    ("2026-09-17", 9, 10),
]
days = [d for d, _, _ in measured]
shares = [r / c for _, r, c in measured]
bars = ax.bar(days, shares, color="#ff7f0e", edgecolor="black")
ax.set_title("(3) Per-day spawn refusal share (measured)")
ax.set_xlabel("Day")
ax.set_ylabel("Refused share")
ax.yaxis.set_major_formatter(PercentFormatter(1.0))
for bar, (_, r, c) in zip(bars, measured):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
            f"{r}/{c}", ha="center", fontsize=8)
ax.set_ylim(0, max(shares) * 1.25)

# --- Panel 4: histogram of body_len, log x-axis, storm vs other ---
ax = axes[1, 1]
lens_storm = storm["body_len"].dropna().values
lens_other = df[~df["body_md5"].isin(STORM_DIGESTS)]["body_len"].dropna().values
bins = np.logspace(np.log10(max(1, df["body_len"].min())), np.log10(df["body_len"].max()), 40)
ax.hist(lens_other, bins=bins, alpha=0.6, label=f"other rows (n={len(lens_other)})", color="gray")
ax.hist(lens_storm, bins=bins, alpha=0.7, label=f"storm digests (n={len(lens_storm)})", color="#d62728")
ax.set_xscale("log")
ax.set_title("(4) body_len histogram (log x-axis)")
ax.set_xlabel("body_len (chars)")
ax.set_ylabel("Rows")
ax.legend(fontsize=8)
# annotate the two storm digest peaks
for d, label in [(CHAT_DIGEST, "96-char chat"), (SPAWN_DIGEST, "384-char spawn")]:
    sub = storm[storm["body_md5"] == d]["body_len"]
    if len(sub):
        ax.axvline(sub.median(), color="black", linestyle="--", linewidth=1)
        ax.text(sub.median(), ax.get_ylim()[1] * 0.9, label, rotation=90,
                fontsize=7, ha="right", va="top")

fig.tight_layout()
fig.savefig(OUT, dpi=150)
print("saved", OUT)
