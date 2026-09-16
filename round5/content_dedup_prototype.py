#!/usr/bin/env python3
"""content_dedup_prototype.py — Lane 1 (wave 3): content-hash dedup prototype.

Demonstrates, on COPIED aggregate data (never the live ingest path), what a
content-hash idempotency layer would collapse: N distinct message rows carrying
byte-identical bodies -> 1 logical message.

Input: CSV with columns body_md5,body_len,msgs,bindings,first_seen,last_seen
Output: dedup report — collapse ratio, binding amplification, window stats.

The fix this prototypes (for the real ingest path, to be built separately):
  1. On ingest, compute md5(normalized_body) per inbound message.
  2. If the same (channel, body_md5) was accepted within WINDOW (e.g. 10 min),
     attach to the existing logical message instead of creating a new row and
     re-driving the full completion pipeline.
  3. Backfill/propagate provider_message_id so the existing UNIQUE constraint
     on (provider, provider_channel_id, provider_message_id) can actually fire.
"""
import csv, sys
from datetime import datetime, timezone

WINDOW_MIN = 10  # idempotency window under test

def parse_ts(s):
    # ISO like 2026-09-16T05:58:05.903055+00:00 ; empty -> None
    if not s or not s.strip():
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None

def main(path):
    rows = list(csv.DictReader(open(path)))
    total_msgs = sum(int(r["msgs"]) for r in rows)
    total_bindings = sum(int(r["bindings"]) for r in rows)
    distinct_bodies = len(rows)
    # collapse: one logical message per distinct body
    collapsed = distinct_bodies
    saved_rows = total_msgs - collapsed
    saved_bindings = total_bindings - sum(1 for r in rows if int(r["bindings"]) > 0)

    print(f"input rows (copied aggregates): {len(rows)} distinct bodies")
    print(f"total message rows:              {total_msgs}")
    print(f"total binding rows:              {total_bindings}")
    print(f"after content-hash dedup:        {collapsed} logical messages")
    print(f"message rows eliminated:         {saved_rows} "
          f"({100.0*saved_rows/max(total_msgs,1):.1f}% collapse)")
    print(f"binding rows eliminated:         {saved_bindings}")
    print(f"idempotency window under test:   {WINDOW_MIN} min")
    print()
    print(f"{'body_md5':10s} {'len':>5s} {'msgs':>5s} {'bnd':>4s} "
          f"{'span_min':>8s} {'rate/min':>8s}  verdict")
    for r in sorted(rows, key=lambda r: -int(r["msgs"])):
        n = int(r["msgs"]); b = int(r["bindings"])
        t0, t1 = parse_ts(r["first_seen"]), parse_ts(r["last_seen"])
        span = (t1 - t0).total_seconds()/60 if t0 and t1 else 0
        rate = n/max(span, 1e-9)
        verdict = "REPLAY-STORM" if rate > 2 and n >= 10 else ("replay" if n >= 10 else "ok")
        print(f"{r['body_md5'][:8]:10s} {r['body_len']:>5s} {n:>5d} {b:>4d} "
              f"{span:>8.1f} {rate:>8.1f}  {verdict}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/dev/stdin")
