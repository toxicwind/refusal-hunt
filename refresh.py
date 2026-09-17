"""refresh.py: first-class parquet paradigm for the spawn ledger.
Usage: python3 refresh.py new_rows.csv
  - appends rows (same schema as spawns.csv), dedupes on spawn_id, re-sorts, rewrites spawns.parquet (snappy)
  - every op timed at us resolution via utime, logged to timings.jsonl
Schema: spawn_id,created_at,secs,status,agent_type,depth,prompt_len,fr_len,refused
  status: 0=completed 1=errored | agent_type: 0=null 1=browser_task 2=deep_research
  refused: 1 if final_response md5 == b4aefd29108f232f9c0d5a4b030215c1 (never store the string itself)
"""
import sys, os
import pandas as pd
from utime import span, log_event

HERE = os.path.dirname(os.path.abspath(__file__))
PARQUET = os.path.join(HERE, "spawns.parquet")

def main():
    if len(sys.argv) != 2:
        print("usage: refresh.py new_rows.csv"); sys.exit(2)
    with span("parquet_read", PARQUET):
        df = pd.read_parquet(PARQUET)
    n0 = len(df)
    with span("csv_read", sys.argv[1]):
        new = pd.read_csv(sys.argv[1])
    with span("merge_dedupe_sort", f"base={n0} new={len(new)}"):
        df = (pd.concat([df, new], ignore_index=True)
                .drop_duplicates("spawn_id")
                .sort_values("spawn_id")
                .reset_index(drop=True))
    with span("parquet_write_snappy", PARQUET):
        df.to_parquet(PARQUET, engine="pyarrow", compression="snappy", index=False)
    added = len(df) - n0
    log_event("refresh_done", f"rows {n0}->{len(df)} (+{added})",
              extra={"refused_total": int(df.refused.sum())})
    print(f"rows {n0}->{len(df)} (+{added}), refused_total={int(df.refused.sum())}")

if __name__ == "__main__":
    main()
