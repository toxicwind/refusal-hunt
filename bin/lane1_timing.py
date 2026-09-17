#!/usr/bin/env python3
"""Lane 1 (direct): storm timing + applied-then-starts correlation.
Builds 5-min storm time series from storm_full.parquet, finds burst onsets
(first storm bucket after >=30 min quiet), emits onset list for DB correlation.
Output: /home/hatch/workspace/refusal-hunt/storm-lanes/lane1.json
"""
import json
import pyarrow.parquet as pq
import pyarrow.compute as pc
from datetime import datetime, timezone, timedelta

PARQUET = "/home/hatch/workspace/refusal-hunt/storm-lanes/../parquet-20260916/storm_full.parquet"
OUT = "/home/hatch/workspace/refusal-hunt/storm-lanes/lane1.json"

t = pq.read_table(PARQUET)
print(f"rows={t.num_rows} cols={t.column_names}")

# created_at -> python datetimes
cats = t.column("created_at").to_pylist()
def to_dt(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    # string form
    try:
        s = str(v)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        d = datetime.fromisoformat(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None

rows = []
for i in range(t.num_rows):
    d = to_dt(cats[i])
    if d is None:
        continue
    rows.append({
        "ts": d,
        "source": t.column("source")[i].as_py(),
        "kind": t.column("kind")[i].as_py(),
        "is_storm": bool(t.column("is_storm_sig")[i].as_py()),
        "md5": t.column("body_md5")[i].as_py(),
    })
rows.sort(key=lambda r: r["ts"])
print(f"parseable={len(rows)} range={rows[0]['ts'].isoformat()}..{rows[-1]['ts'].isoformat()}")

# 5-min buckets over storm rows only
BUCKET = timedelta(minutes=5)
storm_rows = [r for r in rows if r["is_storm"]]
t0 = min(r["ts"] for r in storm_rows).replace(second=0, microsecond=0)
t0 -= timedelta(minutes=t0.minute % 5)
buckets = {}
for r in storm_rows:
    b = t0 + ((r["ts"] - t0) // BUCKET) * BUCKET
    buckets.setdefault(b, []).append(r)

series = sorted(buckets.items())
print(f"nonempty_buckets={len(series)}")

# burst onsets: bucket with storm rows where previous 6 buckets (30 min) are empty
onsets = []
for i, (b, rs) in enumerate(series):
    quiet = True
    for j in range(1, 7):
        prev = b - j * BUCKET
        if prev in buckets:
            quiet = False
            break
    if quiet:
        onsets.append({
            "onset_bucket": b.isoformat(),
            "n_rows": len(rs),
            "by_source": {s: sum(1 for r in rs if r["source"] == s) for s in set(r["source"] for r in rs)},
            "by_kind": {k: sum(1 for r in rs if r["kind"] == k) for k in set(r["kind"] for r in rs)},
            "first_ts": min(r["ts"] for r in rs).isoformat(),
            "last_ts": max(r["ts"] for r in rs).isoformat(),
        })

# also: top-10 busiest buckets overall
top = sorted(series, key=lambda kv: len(kv[1]), reverse=True)[:10]
top_buckets = [{"bucket": b.isoformat(), "n": len(rs),
                "by_source": {s: sum(1 for r in rs if r["source"] == s) for s in set(r["source"] for r in rs)}}
               for b, rs in top]

# per-source totals and hourly histogram (UTC)
from collections import Counter
src_tot = Counter(r["source"] for r in storm_rows)
hourly = Counter(r["ts"].strftime("%Y-%m-%dT%H") for r in storm_rows)

result = {
    "lane": 1,
    "method": "direct-by-main-agent-after-worker-timeout",
    "parquet": PARQUET,
    "n_rows_parquet": t.num_rows,
    "n_parseable": len(rows),
    "n_storm_rows": len(storm_rows),
    "time_range": [rows[0]["ts"].isoformat(), rows[-1]["ts"].isoformat()],
    "bucket_minutes": 5,
    "n_nonempty_buckets": len(series),
    "storm_by_source": dict(src_tot),
    "hourly_utc": dict(sorted(hourly.items())),
    "burst_onsets_30min_quiet": onsets,
    "n_onsets": len(onsets),
    "top10_buckets": top_buckets,
}
with open(OUT, "w") as f:
    json.dump(result, f, indent=2)
print(f"wrote {OUT}: {len(onsets)} onsets, top bucket n={top_buckets[0]['n'] if top_buckets else 0}")
for o in onsets:
    print("ONSET", o["onset_bucket"], "n=", o["n_rows"], o["by_source"])
