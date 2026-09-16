#!/usr/bin/env python3
"""Storm dataframe analysis — 2026-09-16.
Data: agent.subagent_spawns 48h hourly aggregates + parent retry stats,
      queried via muse.db (hand-embedded below; source queries in comments).
Builds pandas DataFrames, computes burst/timing stats, writes parquet.
No refusal literals stored anywhere — hashes and structural counts only.
"""
import subprocess
import sys
from datetime import datetime, timezone, timedelta

import pandas as pd

print("python:", sys.version.split()[0])
print("pandas:", pd.__version__)
# subprocess usage per task order: verify parquet tooling via a child process
r = subprocess.run(["python3", "-c", "import pyarrow; print(pyarrow.__version__)"],
                   capture_output=True, text=True)
print("pyarrow (via subprocess):", r.stdout.strip())

# --- Hourly spawn/refusal aggregates, 48h (muse.db Q1) ---
# SELECT (created_at/3600) hr_epoch, count(*), refused-via-md5, avg(completed-completed_at) ...
hourly = [
    (497046, 5, 0, 68), (497047, 7, 1, 41), (497048, 3, 0, 118),
    (497049, 58, 0, 838), (497050, 21, 0, 911), (497051, 22, 0, 453),
    (497057, 44, 0, 1900), (497058, 22, 0, 1312), (497059, 29, 0, 2034),
    (497060, 16, 0, 566), (497061, 2, 0, 379), (497062, 13, 0, 532),
    (497063, 14, 0, 880), (497064, 30, 0, 950), (497065, 25, 0, 496),
    (497066, 9, 0, 214), (497067, 39, 0, 674), (497068, 8, 5, 415),
    (497070, 18, 16, 48), (497071, 3, 3, 1),
    (497091, 6, 6, 1), (497092, 14, 8, 2), (497093, 13, 13, 4),
]
df = pd.DataFrame(hourly, columns=["hr_epoch", "n", "refused", "avg_dur_s"])
mdt = timezone(timedelta(hours=-6))
df["hr_mdt"] = df["hr_epoch"].apply(
    lambda e: datetime.fromtimestamp(e * 3600, tz=timezone.utc).astimezone(mdt).strftime("%m-%d %H:00"))
df["refusal_rate"] = (df["refused"] / df["n"]).round(3)
df["genuine"] = df["n"] - df["refused"]

print("\n=== hourly storm table (MDT) ===")
print(df[["hr_mdt", "n", "refused", "refusal_rate", "avg_dur_s"]].to_string(index=False))

total = df["n"].sum()
tot_ref = df["refused"].sum()
print(f"\n48h totals: {total} spawns, {tot_ref} canonical refusals ({tot_ref/total:.1%})")

# Burst structure: contiguous refused>0 hours vs quiet hours
df["storm_hr"] = df["refused"] > 0
runs, cur = [], 0
for v in df["storm_hr"]:
    if v:
        cur += 1
    elif cur:
        runs.append(cur); cur = 0
if cur:
    runs.append(cur)
print("storm-hour bursts (lengths in hours):", runs)
quiet = df[~df["storm_hr"]]
print(f"quiet hours: {len(quiet)} with {quiet['n'].sum()} genuine spawns, "
      f"{quiet['refused'].sum()} refusals")

# Intermittency inside the worst recent hour: 497092 had 8 refused / 14 total
worst = df.loc[df["refusal_rate"].idxmax()]
print(f"peak refusal hour: {worst['hr_mdt']} rate={worst['refusal_rate']:.0%} "
      f"({worst['refused']}/{worst['n']})")
mixed = df[(df["refused"] > 0) & (df["genuine"] > 0)]
print(f"mixed hours (genuine AND refused side by side): {len(mixed)} -> "
      f"classifier is intermittent, not blanket, within the hour")

# --- Duration separation (muse.db: group by md5=canonical) ---
dur = pd.DataFrame([
    {"outcome": "refused_canonical", "n": 52, "avg_s": 2.2, "min_s": 0, "max_s": 6},
    {"outcome": "genuine", "n": 365, "avg_s": 846.9, "min_s": 1, "max_s": 10940},
    {"outcome": "null_body_inflight", "n": 4, "avg_s": 41.3, "min_s": 8, "max_s": 58},
])
print("\n=== duration separation ===")
print(dur.to_string(index=False))
print("verdict: refused max 6s vs genuine avg 847s — duration<10s is a "
      "mechanical refusal tell (supplements md5).")

# --- Parent retry behavior after receiving the prohibition-carrying refusal ---
# WITH lead() over parent: 52 refused events, 9 parents hit
retry = {"refused_events": 52, "parents_hit": 9, "avg_mins_to_next": 38.5,
         "next_also_refused": 40, "terminal_no_retry": 8}
retried = retry["refused_events"] - retry["terminal_no_retry"]
print("\n=== parent behavior after canonical refusal ===")
print(f"parents receiving the prohibition text: {retry['parents_hit']}")
print(f"retried anyway: {retried}/{retry['refused_events']} "
      f"({retried/retry['refused_events']:.0%}) after avg {retry['avg_mins_to_next']} min")
print(f"of retries, refused again: {retry['next_also_refused']}/{retried} "
      f"({retry['next_also_refused']/retried:.0%})")
print(f"terminal (no retry): {retry['terminal_no_retry']}/{retry['refused_events']} "
      f"({retry['terminal_no_retry']/retry['refused_events']:.0%})")
print("verdict: the embedded prohibition has ~no behavioral authority over "
      "parents (84% retry); the classifier refuses 91% of retries regardless.")

# --- Chat-level surface (muse.db Q3/Q4) ---
chat = pd.DataFrame([
    {"surface": "assistant turns, md5 582bcbd0 (96ch)", "n": 438},
    {"surface": "assistant turns, empty body", "n": 282},
    {"surface": "user turns echoing the 96ch refusal byte-identically", "n": 1},
])
print("\n=== chat-level refusal surface 48h ===")
print(chat.to_string(index=False))
print("verdict: chat refusal body is a DIFFERENT 96ch template carrying no "
      "prohibition phrasing; echo-replay of refusal-as-user is ~nil (1).")

# Persist
out = "/home/hatch/workspace/refusal-hunt/storm-hourly-20260916.parquet"
df.to_parquet(out, index=False)
print("\nwrote", out, f"({len(df)} rows)")
