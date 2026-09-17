"""Storm dataframe builder: ledger -> per-digest per-hour storm analysis parquet.
Quarantine: digests and lengths only, never message bodies.
"""
import os
import time

t0 = time.time()
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

print("pyarrow", pa.__version__, "pandas", pd.__version__, flush=True)
try:
    import tiktoken
    print("tiktoken", tiktoken.__version__, flush=True)
except Exception as e:
    print("tiktoken unavailable:", e, flush=True)

HOME = os.path.expanduser("~")
LEDGER = HOME + "/workspace/refusal-hunt/ledger/anomalies.parquet"
OUTDIR = HOME + "/workspace/refusal-hunt/storm"
os.makedirs(OUTDIR + "/lanes", exist_ok=True)

STORM_DIGESTS = [
    "b4aefd29108f232f9c0d5a4b030215c1",  # 384-char system refusal
    "582bcbd080daeb3f826c45ed4a83b265",  # 96-char assistant variant
]

t = pq.read_table(LEDGER)
df = t.to_pandas()
print("ledger rows:", len(df), "cols:", list(df.columns), flush=True)
df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")

storm = df[df["body_md5"].isin(STORM_DIGESTS)].copy()
print("storm rows:", len(storm), flush=True)
storm["hour"] = storm["created_at"].dt.floor("h")
g = storm.groupby(["body_md5", "hour"], observed=True).size().reset_index(name="n")
g = g.sort_values(["body_md5", "hour"]).reset_index(drop=True)


def flag(s):
    m = s["n"].mean()
    sd = s["n"].std(ddof=0)
    s = s.copy()
    s["burst"] = s["n"] > (m + 3 * sd)
    s["hour_mean"] = m
    s["hour_sd"] = sd
    return s


g = g.groupby("body_md5", group_keys=False).apply(flag)
pq.write_table(
    pa.Table.from_pandas(g, preserve_index=False),
    OUTDIR + "/storm_analysis.parquet",
    compression="zstd",
)
tot = storm.groupby("body_md5").agg(
    n=("body_md5", "size"),
    first=("created_at", "min"),
    last=("created_at", "max"),
)
print(tot.to_string(), flush=True)
print("top-5 peak hours:", flush=True)
print(g.sort_values("n", ascending=False).head(5).to_string(), flush=True)
print("burst hours:", int(g["burst"].sum()), flush=True)
# per-source breakdown of storm rows
print("storm by source:", flush=True)
print(storm.groupby("source").size().to_string(), flush=True)
print("elapsed %.2fs" % (time.time() - t0), flush=True)
