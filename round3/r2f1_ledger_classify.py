#!/usr/bin/env python3
"""R2F1 fallback: classify refused_as_completed spawns from the anomaly ledger
parquet (live DB pool is down). Prints JSON summary and writes r2f1_report.json."""
import json, sys, time
from datetime import datetime, timezone
import pyarrow.parquet as pq

def epoch(v):
    return datetime.fromisoformat(v).timestamp()

LEDGER = "/home/hatch/workspace/refusal-hunt/ledger/anomalies.parquet"
STORM_MD5 = "b4aefd29108f232f9c0d5a4b030215c1"   # 384-char canned refusal
SHORT_MD5 = "582bcbd080daeb3f826c45ed4a83b265"   # 96-char assistant variant
OUT = "/home/hatch/workspace/refusal-hunt/round3/r2f1_report.json"

def main():
    now = time.time()
    t = pq.read_table(LEDGER).to_pylist()
    day = [r for r in t if r.get("created_at") and (now - epoch(r["created_at"])) < 86400]
    refused = [r for r in day if r.get("status") == "completed"
               and r.get("body_md5") in (STORM_MD5, SHORT_MD5)]
    by_digest = {}
    for r in refused:
        by_digest[r["body_md5"]] = by_digest.get(r["body_md5"], 0) + 1
    parents = sorted({r.get("parent_agent_id") for r in refused if r.get("parent_agent_id")})
    report = {
        "ledger_rows": len(t),
        "rows_24h": len(day),
        "refused_as_completed_24h": len(refused),
        "by_digest": by_digest,
        "distinct_parents": len(parents),
        "parents": parents[:20],
        "generated_at": time.time(),
    }
    json.dump(report, open(OUT, "w"), indent=1)
    print(json.dumps(report))
    return 0

if __name__ == "__main__":
    sys.exit(main())
