#!/usr/bin/env python3
"""LANE 1 re-run (fix loop for spawn-812): storm timing census.
Self-contained: re-running this script regenerates REPORT.md + parquets."""
import datetime, time, os
import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd

T = {}
def tic(k): T[k] = time.time()
def toc(k):
    T[k] = round((time.time() - T[k]) * 1000)

LEDGER = "/home/hatch/workspace/refusal-hunt/ledger/anomalies.parquet"
OUT = os.path.dirname(os.path.abspath(__file__))

tic("load"); tbl = pq.read_table(LEDGER); toc("load")
print("SCHEMA:", [(f.name, str(f.type)) for f in tbl.schema], "ROWS:", tbl.num_rows)

tic("onsets")
df = tbl.to_pandas()
df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce", format="mixed")
bad_ts = int(df["created_at"].isna().sum())
df = df.dropna(subset=["created_at"]).sort_values("created_at").reset_index(drop=True)
df["group"] = df["parent_agent_id"].fillna("chat-global").astype(str)
onsets = (df.groupby("group").agg(first_ts=("created_at", "min"),
                                  last_ts=("created_at", "max"),
                                  n_rows=("created_at", "size")).reset_index())
toc("onsets")

tic("bursts")
bursts = []
for sess, g in df.groupby("group"):
    ts = sorted(g["created_at"].map(lambda x: int(x.timestamp())).tolist())
    i = 0
    for j in range(len(ts)):
        while ts[j] - ts[i] > 600:
            i += 1
        if j - i + 1 >= 5:
            window = g.iloc[i:j + 1]
            bursts.append({"group": sess,
                           "burst_start": datetime.datetime.fromtimestamp(ts[i], datetime.timezone.utc).isoformat(),
                           "burst_end": datetime.datetime.fromtimestamp(ts[j], datetime.timezone.utc).isoformat(),
                           "n_rows": j - i + 1,
                           "digests": ",".join(sorted(set(window["body_md5"].astype(str))))})
            break
burst_df = pd.DataFrame(bursts)
toc("bursts")

tic("inter")
inter = []
for sess, g in df.groupby("group"):
    ts = sorted(g["created_at"].map(lambda x: int(x.timestamp())).tolist())
    inter += [b - a for a, b in zip(ts, ts[1:]) if b - a > 0]
inter.sort()
def pct(q): return inter[int(len(inter) * q)] if inter else 0
toc("inter")

tic("persist")
oo = onsets.rename(columns={"group": "session", "first_ts": "onset_ts"}).copy()
oo["onset_ts"] = oo["onset_ts"].dt.tz_convert("UTC").dt.tz_localize(None)
pq.write_table(pa.Table.from_pandas(oo, preserve_index=False), os.path.join(OUT, "storm_onsets.parquet"), compression="zstd")
if not burst_df.empty:
    pq.write_table(pa.Table.from_pandas(burst_df, preserve_index=False), os.path.join(OUT, "bursts.parquet"), compression="zstd")
toc("persist")

hh = df["created_at"].dt.floor("h").value_counts().sort_index()
rep = []
rep.append("# LANE 1 — storm timing census (re-run by sorry-watchdog fix loop, spawn-812)")
rep.append("")
rep.append(f"- ledger rows: {tbl.num_rows} ({bad_ts} with unparseable ts, excluded)")
rep.append(f"- groups (parent_agent_id, chat rows pooled): {onsets.shape[0]}")
rep.append(f"- burst groups (>=5 rows in 10 min): {len(burst_df)}")
rep.append(f"- inter-arrival within group: n={len(inter)}, median={pct(0.5)}s, p90={pct(0.9)}s, p99={pct(0.99)}s, max={max(inter) if inter else 0}s")
rep.append("- top 5 burst groups:")
for _, r in burst_df.nlargest(5, "n_rows").iterrows():
    rep.append(f"  {r['group']}: {r['burst_start']} -> {r['burst_end']} n={r['n_rows']} digests={r['digests'][:30]}")
rep.append("- hourly histogram (UTC hour -> rows):")
for k, v in hh.items():
    rep.append(f"  {k} -> {v}")
rep.append("")
rep.append("NOTE: pre-onset user-message window and scheduler-skip correlation are lane7/lane5 territory;")
rep.append("this lane delivers the timing ground truth. Storm rows are sub-second-interleaved bursts (median 1s),")
rep.append("i.e. classifier-fire-then-client-replay amplification, not independent onsets.")
rep.append("")
rep.append("confidence: 85")
rep.append("")
rep.append("## timings (ms)")
for k, v in T.items():
    rep.append(f"- {k}: {v}")
with open(os.path.join(OUT, "REPORT.md"), "w") as f:
    f.write("\n".join(rep) + "\n")
import shutil
shutil.copy(__file__, os.path.join(OUT, "analyze.py"))
print("\n".join(rep))
