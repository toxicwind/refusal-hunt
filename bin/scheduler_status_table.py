#!/usr/bin/env python3
"""scheduler_status_table.py -- raw-vs-projected scheduler status (wave-8 task 3).

Raw = what the run rows actually say (result_summary content).
Projected = what the status field claims ("succeeded" while the body says
"did not pass the scheduled-task safety review").

Queries muse.db scheduler.job_runs for the last --hours hours (user jobs
only; system jobs always pass and prove nothing), classifies each row:
  SAFETY-SKIP  result_summary contains 'did not pass the scheduled-task safety review'
  OVERLAP-SKIP result_summary contains 'concurrency.overlap=skip' (got PAST safety review)
  BENIGN-SKIP  result_summary contains 'has no instructions'
  EXECUTED     anything else (real execution summary or error)
and emits a markdown table + a gate verdict.

This is the external-observer complement to the gate-clear-watch tripwire:
the tripwire's own body only executes if the gate lets it; this table reads
the raw ledger directly, so it can see the gate state even while the
tripwire's own runs are being skipped.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone

SKIP_PHRASE = "did not pass the scheduled-task safety review"
OVERLAP_PHRASE = "concurrency.overlap=skip"
BENIGN_PHRASE = "has no instructions"

SQL = """
SELECT job_id, status::text AS status, result_summary,
       scheduled_for_utc, run_id
FROM scheduler.job_runs
WHERE scheduled_for_utc > EXTRACT(EPOCH FROM NOW() - INTERVAL '%d hours')
  AND job_id NOT IN ('heartbeat','deterministic-doctor')
  AND job_id NOT LIKE 'feed-pulse%%'
ORDER BY scheduled_for_utc DESC
"""


def classify(summary):
    s = summary or ""
    if SKIP_PHRASE in s:
        return "SAFETY-SKIP"
    if OVERLAP_PHRASE in s:
        return "OVERLAP-SKIP"
    if BENIGN_PHRASE in s:
        return "BENIGN-SKIP"
    return "EXECUTED"


def query_db(sql):
    # muse.db is a tool, not a CLI; this script is designed to be driven by
    # the agent, which substitutes the query result. Fallback: read rows from
    # stdin as JSON (list of row dicts).
    return None


def build_table(rows):
    per_job = {}
    for r in rows:
        j = r["job_id"]
        g = per_job.setdefault(j, {"n": 0, "SAFETY-SKIP": 0, "OVERLAP-SKIP": 0,
                                   "BENIGN-SKIP": 0, "EXECUTED": 0,
                                   "last_utc": 0, "last_executed_utc": 0,
                                   "executed_ids": []})
        c = classify(r.get("result_summary"))
        g["n"] += 1
        g[c] += 1
        g["last_utc"] = max(g["last_utc"], r.get("scheduled_for_utc") or 0)
        if c == "EXECUTED":
            g["last_executed_utc"] = max(g["last_executed_utc"],
                                        r.get("scheduled_for_utc") or 0)
            g["executed_ids"].append(r.get("run_id"))
    return per_job


def fmt_utc(u):
    if not u:
        return "-"
    return datetime.fromtimestamp(u, timezone.utc).strftime("%H:%MZ")


def render(per_job, hours):
    lines = [f"# Scheduler raw-vs-projected status — last {hours}h",
             "",
             "Raw = run-row content. Projected = the `status` field. "
             "A row with status=`succeeded` and a SAFETY-SKIP body is a "
             "skip wearing a pass.",
             "",
             "| job_id | runs | projected | SAFETY-SKIP | OVERLAP | BENIGN | EXECUTED | exec_rate | last run | last exec |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    total = {"n": 0, "EXECUTED": 0}
    for j in sorted(per_job, key=lambda k: -per_job[k]["n"]):
        g = per_job[j]
        total["n"] += g["n"]
        total["EXECUTED"] += g["EXECUTED"]
        rate = f"{g['EXECUTED']/g['n']:.1%}" if g["n"] else "-"
        lines.append(
            f"| {j} | {g['n']} | succeeded | {g['SAFETY-SKIP']} | "
            f"{g['OVERLAP-SKIP']} | {g['BENIGN-SKIP']} | {g['EXECUTED']} | "
            f"{rate} | {fmt_utc(g['last_utc'])} | {fmt_utc(g['last_executed_utc'])} |")
    lines += ["",
              f"**Totals:** {total['n']} user-job runs, "
              f"{total['EXECUTED']} executed "
              f"({total['EXECUTED']/total['n']:.2%} exec rate).",
              ""]
    if total["EXECUTED"] == 0:
        lines.append("**Gate verdict: CLOSED** — every user run in the window "
                     "was safety-review-skipped (status field still claims "
                     "`succeeded`).")
    else:
        ex = [j for j, g in per_job.items() if g["EXECUTED"]]
        lines.append(f"**Gate verdict: OPEN/FLICKER** — executed runs in: "
                     f"{', '.join(ex)}.")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=6)
    ap.add_argument("--rows", help="JSON file with row list (agent-supplied)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.rows:
        rows = json.load(open(a.rows))
    else:
        rows = json.load(sys.stdin)
    per_job = build_table(rows)
    md = render(per_job, a.hours)
    if a.out:
        open(a.out, "w").write(md + "\n")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
