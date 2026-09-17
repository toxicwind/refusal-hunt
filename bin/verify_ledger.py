#!/usr/bin/env python3
"""Verify the anomaly ledger: schema, compression, counts, quarantine, timestamps."""
import json, os
import pyarrow.parquet as pq

LEDGER = os.path.expanduser("~/workspace/refusal-hunt/ledger/anomalies.parquet")
STATUS = os.path.expanduser("~/workspace/refusal-hunt/ledger/LEDGER_STATUS.json")

st = json.load(open(STATUS))
print("STATUS total_rows:", st["total_rows"])
print("STATUS newest:", st.get("newest_created_at"))

pf = pq.ParquetFile(LEDGER)
print("num_rows:", pf.metadata.num_rows, "num_row_groups:", pf.metadata.num_row_groups)
print("created_by:", pf.metadata.created_by)
codecs = {pf.metadata.row_group(i).column(j).compression
          for i in range(pf.metadata.num_row_groups)
          for j in range(pf.metadata.num_columns)}
print("compressions:", codecs)

t = pf.read()
print("schema:", t.schema)
df = t.to_pandas()
print("columns:", list(df.columns))
print("rows:", len(df))
print("by_source_digest:\n", df.groupby(["source", "body_md5"]).size().to_string())
print("dup(source,id):", int(df.duplicated(subset=["source", "id"]).sum()))
print("null body_md5:", int(df["body_md5"].isna().sum()))
if "body" in df.columns:
    print("BODY COLUMN PRESENT - quarantine violated, non-null bodies:", int(df["body"].notna().sum()))
else:
    print("no body column: quarantine holds")
print("created_at min:", df["created_at"].min(), "max:", df["created_at"].max())
print("body_len values:", sorted(df["body_len"].unique().tolist()))
print("status values:", df["status"].dropna().unique().tolist())
