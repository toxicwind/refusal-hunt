#!/usr/bin/env python3
"""One-time migration: normalize created_at to ISO-8601 T-format in the ledger.
Same rows, same dedup keys, format-only change so newest_created_at is correct."""
import os, sys
sys.path.insert(0, os.path.expanduser("~/workspace/refusal-hunt/bin"))
from anomaly_ledger import norm_ts, LEDGER_PATH  # noqa: E402

import pandas as pd

df = pd.read_parquet(LEDGER_PATH)
before = df["created_at"].copy()
df["created_at"] = df["created_at"].map(norm_ts)
changed = int((df["created_at"] != before).sum())
df.to_parquet(LEDGER_PATH, compression="zstd", index=False)
print(f"rows={len(df)} normalized={changed} newest={df['created_at'].max()}")
print("dup(source,id):", int(df.duplicated(subset=["source", "id"]).sum()))
