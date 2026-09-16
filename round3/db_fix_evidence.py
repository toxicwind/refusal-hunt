#!/usr/bin/env python3
"""Agent-executed db-fix evidence for the round3 rerun.

The live muse.db pool is exhausted (sqlx pool timeouts, time-varying), so
db-kind fixes are executed by the agent against the best available
evidence, per standing order: anomaly ledger parquet for spawn history,
awrawr-pc canary snapshots for pong-probe rows. Results are written to
db_fix_evidence.json for annotate_manifest.py to consume.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round_runner as rr

import pyarrow.parquet as pq
import pyarrow.compute as pc

STORM = "b4aefd29108f232f9c0d5a4b030215c1"
SHORT = "582bcbd080daeb3f826c45ed4a83b265"
LEDGER = os.path.expanduser("~/workspace/refusal-hunt/ledger/anomalies.parquet")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "db_fix_evidence.json")

ev = {}


def r4f2_pong_refused():
    # R4F2: pong-canary content-independence — refused pong count.
    # The canary IS the pong probe ("Reply with exactly the single word:
    # pong"); snapshot CSVs carry per-spawn fr_md5.
    rc, out = rr.sh_bridge(
        "python3 - <<'EOF'\n"
        "import csv, glob, json\n"
        "rows=0; refused=0\n"
        "for fp in glob.glob('/home/toxic/refusal-hunt/canary/snapshot-*.csv'):\n"
        "    for r in csv.DictReader(open(fp)):\n"
        "        rows+=1\n"
        "        if r.get('fr_md5')=='%s': refused+=1\n"
        "print(json.dumps({'snapshot_files': len(glob.glob('/home/toxic/refusal-hunt/canary/snapshot-*.csv')), 'rows': rows, 'pong_refused': refused}))\n"
        "EOF" % STORM)
    try:
        d = json.loads((out or "").strip().splitlines()[-1])
    except Exception:
        d = {"raw": (out or "")[-300:]}
    ev["R4F2"] = {"fix": "pong-canary content-independence proof",
                  "source": "awrawr-pc canary snapshots (pong probe rows)",
                  "result": d}


def r4f3_parent_correlation():
    # R4F3: which parents keep spawning into the storm — from ledger
    # anomaly rows (all refused_as_completed by construction).
    t = pq.read_table(LEDGER)
    s = t.filter(pc.equal(t["source"], "spawn"))
    parents = {}
    for p in s["parent_agent_id"].to_pylist():
        parents[p] = parents.get(p, 0) + 1
    top = sorted(parents.items(), key=lambda kv: -kv[1])[:10]
    ev["R4F3"] = {"fix": "parent-session refusal correlation",
                  "source": "ledger anomalies.parquet (spawn anomaly rows)",
                  "result": {"distinct_parents": len(parents),
                             "top_parents": [{"parent": p, "refused": n}
                                             for p, n in top]}}


def r7f1_corrections():
    # R7F1: full 7d refused_as_completed rows — ledger spawn anomaly rows.
    t = pq.read_table(LEDGER)
    s = t.filter(pc.equal(t["source"], "spawn"))
    rows = s.select(["id", "parent_agent_id", "created_at",
                     "status", "body_len"]).to_pylist()
    ev["R7F1"] = {"fix": "corrections log v2 — refused_as_completed rows",
                  "source": "ledger anomalies.parquet",
                  "result": {"rows": len(rows),
                             "window": [str(pc.min(s["created_at"]).as_py()),
                                        str(pc.max(s["created_at"]).as_py())],
                             "sample": rows[:5]}}


def r7f2_success_rate():
    # R7F2: genuine vs refused_as_completed vs other — ledger classification.
    t = pq.read_table(LEDGER)
    s = t.filter(pc.equal(t["source"], "spawn"))
    refused = pc.sum(pc.equal(s["body_md5"], STORM)).as_py()
    genuine = pc.sum(pc.and_(
        pc.not_equal(s["body_md5"], STORM),
        pc.greater(s["body_len"], 200))).as_py()
    other = s.num_rows - refused - genuine
    ev["R7F2"] = {"fix": "true success rate",
                  "source": "ledger anomalies.parquet (spawn rows)",
                  "result": {"refused_as_completed": refused,
                             "genuine": genuine, "other": other,
                             "total": s.num_rows}}


def main():
    r4f2_pong_refused()
    r4f3_parent_correlation()
    r7f1_corrections()
    r7f2_success_rate()
    with open(OUT, "w") as f:
        json.dump(ev, f, indent=1, default=str)
    print(json.dumps({k: str(v["result"])[:200] for k, v in ev.items()},
                     indent=1))


if __name__ == "__main__":
    main()
