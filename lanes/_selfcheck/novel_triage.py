"""Triage: (1) find the true session key; (2) classify the ~50 novel digest rows."""
import os
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pandas as pd

t = pq.read_table(os.path.expanduser("~/workspace/refusal-hunt/ledger/anomalies.parquet"))
df = t.to_pandas()
KNOWN = {"582bcbd080daeb3f826c45ed4a83b265", "b4aefd29108f232f9c0d5a4b030215c1"}

print("=== session-key candidates ===")
for c in ["source", "parent_agent_id", "child_agent_id"]:
    print(c, "distinct:", df[c].nunique())
print("top parent_agent_id:")
print(df["parent_agent_id"].value_counts().head(10).to_dict())
print("source mix:", df["source"].value_counts().to_dict())
print("status mix:", df["status"].value_counts().to_dict())

print("=== novel digest rows ===")
nov = df[~df["body_md5"].isin(KNOWN)].copy()
print("novel rows:", len(nov), "| distinct digests:", nov["body_md5"].nunique())
print("body_len distribution:")
print(nov["body_len"].value_counts().head(20).to_dict())
print("source:", nov["source"].value_counts().to_dict())
print("status:", nov["status"].value_counts().to_dict())
nov["created_at"] = pd.to_datetime(nov["created_at"], format="mixed", utc=True)
print("time range:", nov["created_at"].min(), "->", nov["created_at"].max())
print("token_count describe:", nov["token_count"].describe().to_dict())
# same digest, multiple rows?
dup = nov["body_md5"].value_counts()
print("novel digests appearing >1 time:", dup[dup > 1].to_dict())
out = os.path.expanduser("~/workspace/refusal-hunt/lanes/_selfcheck/novel_rows.parquet")
pq.write_table(t.filter(pc.invert(pc.is_in(t.column("body_md5"),
            value_set=__import__("pyarrow").array(list(KNOWN))))), out, compression="zstd")
print("wrote", out)
