#!/usr/bin/env python3
"""echo_watch.py -- duplicate/echo detector for the client replay bug.

The client replays refused/failed turns as brand-new user messages, so one
legitimate request becomes dozens of identical rows. This tool scans
runtime.messages + runtime.channel_message_bindings for
provider/channel/body/time duplicates in the last 60 minutes, using body-md5
grouping performed INSIDE the database (via the muse.db tool) so body text
never leaves the DB: only digests, counts, and timestamps flow downstream.

Usage (two steps, run by the invoking agent):
  1. Run each statement in SQL_QUERIES through the muse.db tool (read-only).
  2. Convert each result set to JSONL rows tagged with "query":
       {"query": "msg_stats",  ...row...}
       {"query": "msg_dups",   ...row...}
       {"query": "bind_stats", ...row...}
       {"query": "bind_dups",  ...row...}
     and pipe the concatenated stream into this script:
       cat rows.jsonl | echo_watch.py

The script prints a report (total rows, distinct bodies, top-5 most-repeated
bodies with counts -- digests only, never body text) and writes the same
report to ~/workspace/refusal-hunt/echo-reports/<utc-timestamp>.txt.

SAFETY: this script opens no database connection, issues no SQL, and never
deletes or modifies rows. It reads stdin, writes stdout, and creates exactly
one new report file (additive, forward-only).
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "bin"))
try:
    from echo_collapse import KNOWN_STORM_MD5
except Exception:
    # Digest-only fallback: never store the bodies (loop-fuel rule).
    KNOWN_STORM_MD5 = {
        "b4aefd29108f232f9c0d5a4b030215c1",
        "582bcbd080daeb3f826c45ed4a83b265",
    }

REPORT_DIR = os.path.expanduser("~/workspace/refusal-hunt/echo-reports")
WINDOW = "last 60 minutes"

# Exact SQL the invoking agent runs through the muse.db tool (read-only).
# Body-md5 grouping happens in the database; only digests come out.
SQL_QUERIES = {
    "msg_stats": (
        "SELECT count(*) AS total_messages, "
        "count(DISTINCT md5(coalesce(body, ''))) AS distinct_bodies "
        "FROM runtime.messages "
        "WHERE created_at >= now() - make_interval(mins => 60)"
    ),
    "msg_dups": (
        "SELECT b.provider AS provider, b.channel AS channel, "
        "m.role::text AS role, "
        "md5(coalesce(m.body, '')) AS body_md5, "
        "count(*) AS n, "
        "min(m.created_at) AS first_seen, "
        "max(m.created_at) AS last_seen, "
        "max(length(coalesce(m.body, ''))) AS body_len "
        "FROM runtime.messages m "
        "LEFT JOIN runtime.channel_message_bindings b "
        "ON b.jarvis_message_id = m.message_id "
        "WHERE m.created_at >= now() - make_interval(mins => 60) "
        "GROUP BY b.provider, b.channel, m.role, md5(coalesce(m.body, '')) "
        "HAVING count(*) > 1 "
        "ORDER BY n DESC LIMIT 50"
    ),
    "bind_stats": (
        "SELECT count(*) AS total_bindings, "
        "count(DISTINCT md5(coalesce(provider, '') || '|' || "
        "coalesce(channel, '') || '|' || "
        "coalesce(provider_message_id, ''))) AS distinct_provider_msgs "
        "FROM runtime.channel_message_bindings "
        "WHERE created_at >= now() - make_interval(mins => 60)"
    ),
    "bind_dups": (
        "SELECT provider, channel, provider_message_id, "
        "md5(coalesce(provider, '') || '|' || coalesce(channel, '') || '|' || "
        "coalesce(provider_message_id, '')) AS combo_md5, "
        "count(*) AS n, "
        "min(created_at) AS first_seen, "
        "max(created_at) AS last_seen "
        "FROM runtime.channel_message_bindings "
        "WHERE created_at >= now() - make_interval(mins => 60) "
        "GROUP BY provider, channel, provider_message_id "
        "HAVING count(*) > 1 "
        "ORDER BY n DESC LIMIT 50"
    ),
}


def short(s, n=24):
    s = "" if s is None else str(s)
    return s if len(s) <= n else s[:n] + "..."


def main() -> int:
    buckets = {"msg_stats": [], "msg_dups": [], "bind_stats": [], "bind_dups": []}
    raw = 0
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        raw += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        q = row.get("query")
        if q in buckets:
            buckets[q].append(row)

    now_utc = datetime.now(timezone.utc)
    L = []
    L.append("echo_watch report")
    L.append("generated_utc: " + now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"))
    L.append("window: " + WINDOW)
    L.append("input_rows_consumed: %d" % raw)
    L.append("")

    # ---- messages ----
    ms = buckets["msg_stats"][0] if buckets["msg_stats"] else {}
    total_messages = ms.get("total_messages", 0) or 0
    distinct_bodies = ms.get("distinct_bodies", 0) or 0
    mdups = sorted(buckets["msg_dups"], key=lambda r: r.get("n", 0) or 0, reverse=True)
    echo_message_rows = sum((r.get("n", 0) or 0) - 1 for r in mdups)

    L.append("== runtime.messages (last 60 min) ==")
    L.append("total_rows: %d" % total_messages)
    L.append("distinct_bodies(md5): %d" % distinct_bodies)
    L.append("duplicate_body_groups: %d" % len(mdups))
    L.append("echo_duplicate_rows: %d" % echo_message_rows)
    L.append("")
    L.append("top-5 most-repeated bodies (digest only -- never body text):")
    if not mdups:
        L.append("  (none)")
    for i, r in enumerate(mdups[:5], 1):
        digest = r.get("body_md5", "?")
        storm = " STORM-SIGNATURE" if digest in KNOWN_STORM_MD5 else ""
        L.append(
            "  #%d n=%d md5=%s role=%s provider=%s channel=%s body_len=%s%s"
            % (
                i,
                r.get("n", 0) or 0,
                digest,
                r.get("role", "?"),
                r.get("provider", "?"),
                r.get("channel", "?"),
                r.get("body_len", "?"),
                storm,
            )
        )
        L.append(
            "       first_seen=%s last_seen=%s"
            % (r.get("first_seen", "?"), r.get("last_seen", "?"))
        )
    L.append("")

    # ---- bindings ----
    bs = buckets["bind_stats"][0] if buckets["bind_stats"] else {}
    total_bindings = bs.get("total_bindings", 0) or 0
    distinct_combos = bs.get("distinct_provider_msgs", 0) or 0
    bdups = sorted(buckets["bind_dups"], key=lambda r: r.get("n", 0) or 0, reverse=True)
    echo_binding_rows = sum((r.get("n", 0) or 0) - 1 for r in bdups)

    L.append("== runtime.channel_message_bindings (last 60 min) ==")
    L.append("total_rows: %d" % total_bindings)
    L.append("distinct_provider_channel_msg: %d" % distinct_combos)
    L.append("duplicate_binding_groups: %d" % len(bdups))
    L.append("echo_duplicate_rows: %d" % echo_binding_rows)
    L.append("")
    L.append("top-5 most-repeated binding groups:")
    if not bdups:
        L.append("  (none)")
    for i, r in enumerate(bdups[:5], 1):
        L.append(
            "  #%d n=%d combo_md5=%s provider=%s channel=%s provider_message_id=%s"
            % (
                i,
                r.get("n", 0) or 0,
                r.get("combo_md5", "?"),
                r.get("provider", "?"),
                r.get("channel", "?"),
                short(r.get("provider_message_id"), 32),
            )
        )
        L.append(
            "       first_seen=%s last_seen=%s"
            % (r.get("first_seen", "?"), r.get("last_seen", "?"))
        )
    L.append("")
    L.append("notes: read-only scan. No rows were deleted or modified.")

    report = "\n".join(L) + "\n"

    os.makedirs(REPORT_DIR, exist_ok=True)
    stamp = now_utc.strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(REPORT_DIR, stamp + ".txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)

    sys.stdout.write(report)
    sys.stdout.write("report_file: %s\n" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
