#!/usr/bin/env python3
"""anomaly_ledger.py -- persistent sorry/completed anomaly ledger (parquet-first).

Upserts digest-classified anomaly rows (canned chat responses, fake-completed
spawns) into a zstd parquet ledger. Deduplicates on (source, id). Computes
tiktoken cl100k_base token counts when a body is supplied.

Quarantine: verbatim refusal bodies for the two storm digests NEVER hit disk --
digests and lengths only.

Usage:
    python3 anomaly_ledger.py --rows inbox/2026-09-16T10-40.jsonl [--banner]
    python3 anomaly_ledger.py --banner
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import safe_write  # noqa: E402 -- append-exception guards (fail loud,
                   # keep prior good copy intact)

os.environ.setdefault("TIKTOKEN_CACHE_DIR",
                      os.path.expanduser("~/workspace/refusal-hunt/.tiktoken-cache"))

LEDGER_DIR = os.path.expanduser("~/workspace/refusal-hunt/ledger")
LEDGER_PATH = os.path.join(LEDGER_DIR, "anomalies.parquet")
STATUS_PATH = os.path.join(LEDGER_DIR, "LEDGER_STATUS.json")
QUARANTINED = {"582bcbd080daeb3f826c45ed4a83b265",
               "b4aefd29108f232f9c0d5a4b030215c1"}

SCHEMA_FIELDS = ["source", "id", "created_at", "body_md5", "body_len",
                 "token_count", "status", "parent_agent_id", "child_agent_id",
                 "ingested_at"]


def norm_ts(v):
    if v is None:
        return None
    s = str(v).strip()
    try:
        f = float(s)
        return datetime.datetime.fromtimestamp(
            f, datetime.timezone.utc).isoformat()
    except (ValueError, OverflowError):
        pass
    # normalize any parseable timestamp to ISO-8601 with T separator so
    # string max() over the column is chronological (2026-09-16 fix: mixed
    # "YYYY-MM-DD HH:MM:SS+00" and "YYYY-MM-DDTHH:MM:SS+00:00" formats made
    # newest_created_at pick the wrong row because 'T' > ' ').
    try:
        return datetime.datetime.fromisoformat(s).isoformat()
    except ValueError:
        return s  # unparseable: keep raw


def token_count(text):
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return None


def healthcheck(pd, max_stale_secs):
    """Cross-check the ledger files. Prints JSON, returns exit code:
    0 healthy, 1 stale/drift, 2 unreadable."""
    try:
        actual = len(pd.read_parquet(LEDGER_PATH, columns=["id"]))
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"parquet read failed: {e}"}))
        return 2
    try:
        with open(STATUS_PATH) as fh:
            st = json.load(fh)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"status read failed: {e}"}))
        return 2
    problems = []
    if st.get("total_rows") != actual:
        problems.append(
            f"status total_rows={st.get('total_rows')} != parquet rows={actual}")
    try:
        upd = datetime.datetime.fromisoformat(st.get("updated_at"))
        if upd.tzinfo is None:
            upd = upd.replace(tzinfo=datetime.timezone.utc)
        age = (datetime.datetime.now(datetime.timezone.utc) - upd).total_seconds()
        if age > max_stale_secs:
            problems.append(
                f"status updated_at {age:.0f}s ago (> {max_stale_secs}s): "
                f"writer may be dead")
    except Exception:
        problems.append("status updated_at unparseable")
    ok = not problems
    print(json.dumps({"ok": ok, "parquet_rows": actual,
                      "status_total": st.get("total_rows"),
                      "status_updated_at": st.get("updated_at"),
                      "newest_created_at": st.get("newest_created_at"),
                      "problems": problems}))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default=None)
    ap.add_argument("--banner", action="store_true")
    ap.add_argument("--healthcheck", action="store_true",
                    help="verify parquet row count matches status total_rows and "
                         "status is fresh; exit 0 healthy, 1 stale/drift, 2 unreadable")
    ap.add_argument("--max-stale-secs", type=int, default=1800)
    args = ap.parse_args()
    os.makedirs(LEDGER_DIR, exist_ok=True)

    import pandas as pd  # noqa: E402

    if args.healthcheck:
        raise SystemExit(healthcheck(pd, args.max_stale_secs))

    if os.path.exists(LEDGER_PATH):
        df = pd.read_parquet(LEDGER_PATH)
    else:
        df = pd.DataFrame({c: [] for c in SCHEMA_FIELDS})

    ingested_now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    n_new = 0
    if args.rows:
        recs = []
        with open(args.rows) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                md5 = r.get("body_md5")
                body = r.get("body")
                if md5 in QUARANTINED:
                    body = None  # quarantine: digests + lengths only
                recs.append({
                    "source": r.get("source"),
                    "id": str(r.get("id")),
                    "created_at": norm_ts(r.get("created_at")),
                    "body_md5": md5,
                    "body_len": r.get("body_len"),
                    "token_count": token_count(body) if body else None,
                    "status": r.get("status"),
                    "parent_agent_id": r.get("parent_agent_id"),
                    "child_agent_id": r.get("child_agent_id"),
                    "ingested_at": ingested_now,
                })
        new_df = pd.DataFrame(recs, columns=SCHEMA_FIELDS)
        before = len(df)
        df = pd.concat([df, new_df], ignore_index=True)
        df = df.drop_duplicates(subset=["source", "id"], keep="last")
        n_new = len(df) - before
        # Append-exception guard (2026-09-19, debate 0220db63 slice 1):
        # atomic parquet replace + .bak of the prior good copy. Any
        # failure raises -- never a zero-byte/truncated ledger.
        safe_write.atomic_write_parquet(df, LEDGER_PATH)
        # Fail loudly: re-read and confirm the write actually landed. A
        # mismatch means the ledger writer is broken — never update the
        # status file to claim rows that did not persist (2026-09-17:
        # a worker claimed '152 new rows' while writing nothing).
        verified = len(pd.read_parquet(LEDGER_PATH, columns=["id"]))
        if verified != len(df):
            raise SystemExit(
                f"LEDGER WRITE VERIFICATION FAILED: expected {len(df)} rows, "
                f"parquet has {verified}. Status NOT updated.")

    total = len(df)
    by_key = (df.groupby(["source", "body_md5"]).size().to_dict()
              if total else {})
    status = {
        "ledger": LEDGER_PATH,
        "total_rows": int(total),
        "new_rows_this_run": int(n_new),
        "write_verified": True,
        "by_source_digest": {f"{k[0]}:{k[1][:8]}": int(v)
                             for k, v in by_key.items()},
        "newest_created_at": (str(df["created_at"].max())
                              if total and "created_at" in df else None),
        "updated_at": ingested_now,
    }
    # Append-exception guard: atomic status replace (tmp + fsync +
    # rename). A crash mid-write can never leave a zero-byte
    # LEDGER_STATUS.json behind.
    safe_write.atomic_write_json(STATUS_PATH, status)

    if args.banner or args.rows:
        print(f"LEDGER total={total} new={n_new} write_verified=True "
              f"keys={status['by_source_digest']} "
              f"newest={status['newest_created_at']}")


if __name__ == "__main__":
    main()
