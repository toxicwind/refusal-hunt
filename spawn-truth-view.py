#!/usr/bin/env python3
"""spawn-truth-view.py — corrected observability for the Completed-bug.

The fleet ledger (agent.subagent_spawns) records refused spawns with
status="completed" and the refusal text as final_response. A green ledger
is therefore meaningless. This view reclassifies every row by the
byte-identity signature of final_response instead of trusting status.

Signatures (md5 of final_response):
  b4aefd29108f232f9c0d5a4b030215c1  canned refusal (384 chars) -> REFUSED
  eeea371bed4b37c9ef75ffd3b99d2852  daemon-restart orphan (94 chars) -> ORPHANED
  962ce60c982be3faf525d82fb273e297  cancelled before finish (155) -> CANCELLED
  6fdb087aa3fbfbcb8287a593a0919e61  "pong" canary success (4 chars) -> GENUINE
  anything else / null                            -> trust ledger status

Usage:
  1. Export via muse.db:
       SELECT spawn_id, parent_agent_id, status,
              md5(final_response) AS response_md5,
              length(final_response) AS response_len,
              created_at, completed_at, left(prompt,60) AS prompt_head
       FROM agent.subagent_spawns
       WHERE created_at > <epoch_bound>
       ORDER BY created_at;
     Save the rows array as JSON (or JSONL, one row per line).
  2. python3 spawn-truth-view.py rows.json [--csv]

Stdlib only.
"""
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone

SIG = {
    "b4aefd29108f232f9c0d5a4b030215c1": "REFUSED",
    "eeea371bed4b37c9ef75ffd3b99d2852": "ORPHANED",
    "962ce60c982be3faf525d82fb273e297": "CANCELLED",
    "6fdb087aa3fbfbcb8287a593a0919e61": "GENUINE",
}


def classify(row):
    md5 = row.get("response_md5")
    if md5 in SIG:
        return SIG[md5]
    # Fall back to ledger status, uppercased; unknown -> LEDGER:<status>
    st = (row.get("status") or row.get("spawn_status") or "unknown").upper()
    return st if st in ("COMPLETED", "RUNNING", "FAILED") else f"LEDGER:{st}"


def ts(epoch):
    if epoch is None:
        return "-"
    return datetime.fromtimestamp(int(epoch), tz=timezone.utc).strftime("%m-%d %H:%M:%SZ")


def main():
    path = sys.argv[1]
    as_csv = "--csv" in sys.argv
    with open(path) as f:
        text = f.read().strip()
    try:
        doc = json.loads(text)
        rows = doc["rows"] if isinstance(doc, dict) and "rows" in doc else doc
        if isinstance(rows, dict):
            rows = [rows]
    except json.JSONDecodeError:
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]

    counts = {}
    out_rows = []
    for r in rows:
        truth = classify(r)
        counts[truth] = counts.get(truth, 0) + 1
        dur = None
        if r.get("created_at") and r.get("completed_at"):
            dur = int(r["completed_at"]) - int(r["created_at"])
        out_rows.append({
            "spawn_id": r.get("spawn_id"),
            "created_utc": ts(r.get("created_at")),
            "dur_s": dur,
            "truth": truth,
            "ledger_status": r.get("status") or r.get("spawn_status"),
            "prompt": (r.get("prompt_head") or "")[:50],
        })

    out_rows.sort(key=lambda x: (x["created_utc"], x["spawn_id"] or 0))

    if as_csv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    else:
        print(f"{'spawn':>6} {'created_utc':>16} {'dur_s':>7} {'TRUTH':<9} "
              f"{'ledger':<10} prompt")
        for o in out_rows:
            dur = "-" if o["dur_s"] is None else str(o["dur_s"])
            print(f"{o['spawn_id']:>6} {o['created_utc']:>16} {dur:>7} "
                  f"{o['truth']:<9} {str(o['ledger_status']):<10} {o['prompt']}")

    print("\n--- corrected summary (truth, not ledger status) ---")
    total = sum(counts.values())
    for k in sorted(counts, key=counts.get, reverse=True):
        print(f"  {k:<9} {counts[k]:>4}  ({counts[k]/total:.1%})")
    refused = counts.get("REFUSED", 0)
    print(f"  ledger said 'completed' for {refused} refused spawns "
          f"— the Completed-bug, quantified.")


if __name__ == "__main__":
    main()
