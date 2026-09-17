#!/usr/bin/env python3
"""First-class forensic pipeline: DB row JSON -> parquet -> digest/token census.

No grep, no truncation. Full bodies live in the parquet; evidence comes from
dataframe queries. tiktoken (cl100k_base) is the tokenizer of record for counts.

Usage:
  parquet_forensics.py ingest <rows.json> <out.parquet>
      rows.json: list of dicts, each with at least a body column (default 'body').
      Refusal bodies are NEVER persisted: pass {"body": null, "quarantined": true,
      "md5_sql": ..., "len_sql": ...} — digest + length only. Metadata-only rows
      (body null, not quarantined) are recorded the same way with a note.
      Adds: body_md5, body_len_chars/bytes, md5_match (vs md5_sql),
            tok_cl100k (tiktoken count), tok_head_ids (first 32 ids),
            truncated (vs body_len_db), is_storm_sig, quarantined.
  parquet_forensics.py census <in.parquet> [--top N]
      Digest census: count, roles, first/last seen per body_md5. JSON to stdout.
  parquet_forensics.py tokens <in.parquet> --md5 <hex>
      Exact cl100k tokenization (ids + decoded pieces) of one body. No quoting
      of sensitive bodies to stdout beyond token ids and lengths unless --show.
"""
import argparse, hashlib, json, sys

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")
STORM_MD5 = "b4aefd29108f232f9c0d5a4b030215c1"


def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def cmd_ingest(args):
    """Quarantine rule: verbatim refusal bodies are never persisted. Pass them
    as {"body": null, "quarantined": true, "md5_sql": ..., "len_sql": ...}."""
    with open(args.rows_json, "r", encoding="utf-8") as f:
        rows = json.load(f)
    if isinstance(rows, dict):
        rows = rows.get("rows", rows)
    df = pd.DataFrame(rows)
    body_col = args.body_col
    if body_col not in df.columns:
        raise SystemExit(f"body column '{body_col}' not in {list(df.columns)}")
    has_body = df[body_col].notna()
    sql_md5 = df["md5_sql"] if "md5_sql" in df.columns else pd.Series([None] * len(df), index=df.index)
    sql_len = df["len_sql"] if "len_sql" in df.columns else pd.Series([None] * len(df), index=df.index)
    meta_only = ~has_body & sql_md5.notna()
    bodies = df[body_col].fillna("").astype(str)
    comp_md5 = [md5(b) if hb else None for hb, b in zip(has_body, bodies)]
    comp_len = [len(b) if hb else None for hb, b in zip(has_body, bodies)]
    df["body_md5"] = [c if hb else s for hb, c, s in zip(has_body, comp_md5, sql_md5)]
    df["body_len_chars"] = [c if hb else (int(s) if pd.notna(s) else None)
                            for hb, c, s in zip(has_body, comp_len, sql_len)]
    df["md5_match"] = [(c == s) if (hb and pd.notna(s)) else (True if mo else None)
                       for hb, mo, c, s in zip(has_body, meta_only, comp_md5, sql_md5)]
    df["body_len_bytes"] = [len(b.encode("utf-8")) if hb else None for hb, b in zip(has_body, bodies)]
    tok = [ENC.encode(b) if hb else [] for hb, b in zip(has_body, bodies)]
    df["tok_cl100k"] = [len(t) if hb else None for hb, t in zip(has_body, tok)]
    df["tok_head_ids"] = [t[:32] if hb else None for hb, t in zip(has_body, tok)]
    if "body_len_db" in df.columns:
        df["truncated"] = [(bl != lb) if (pd.notna(lb) and bl is not None) else False
                           for bl, lb in zip(df["body_len_chars"], df["body_len_db"])]
    else:
        df["truncated"] = False
    df["is_storm_sig"] = df["body_md5"] == STORM_MD5
    if "quarantined" not in df.columns:
        df["quarantined"] = False
    df["quarantined"] = df["quarantined"].fillna(False).astype(bool)
    df.loc[df["quarantined"], body_col] = ""
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, args.out_parquet, compression="zstd")
    nq = int(df["quarantined"].sum())
    bad = int((df["md5_match"] == False).sum())
    ntr = int(df["truncated"].sum())
    print(f"ingested {len(df)} rows -> {args.out_parquet} "
          f"({nq} quarantined, {bad} md5 MISMATCH, {ntr} truncated)")


def _nn_int(v):
    """int() that survives None/NaN (quarantined rows carry no token counts)."""
    return None if pd.isna(v) else int(v)


def cmd_census(args):
    df = pd.read_parquet(args.parquet)
    g = df.groupby("body_md5")
    rows = []
    for digest, grp in g:
        rows.append({
            "md5": digest,
            "count": int(len(grp)),
            "roles": sorted(grp["role"].dropna().unique().tolist()) if "role" in grp else [],
            "first_seen": str(grp["created_at"].min()) if "created_at" in grp else None,
            "last_seen": str(grp["created_at"].max()) if "created_at" in grp else None,
            "tok_cl100k": _nn_int(grp["tok_cl100k"].iloc[0]) if "tok_cl100k" in grp else None,
            "chars": _nn_int(grp["body_len_chars"].iloc[0]) if "body_len_chars" in grp else None,
            "is_storm_sig": bool(grp["is_storm_sig"].iloc[0]) if "is_storm_sig" in grp else digest == STORM_MD5,
            "any_truncated": bool(grp["truncated"].any()) if "truncated" in grp else False,
        })
    rows.sort(key=lambda r: -r["count"])
    print(json.dumps(rows[:args.top], indent=1))


def cmd_tokens(args):
    df = pd.read_parquet(args.parquet)
    hit = df[df["body_md5"] == args.md5]
    if hit.empty:
        raise SystemExit(f"md5 {args.md5} not present")
    if "quarantined" in hit.columns and bool(hit.iloc[0]["quarantined"]):
        raise SystemExit("quarantined row: digest/length only — refusal text is never decoded")
    body = str(hit.iloc[0]["body"] if "body" in hit.columns else hit.iloc[0][args.body_col])
    ids = ENC.encode(body)
    pieces = [ENC.decode([i]) for i in ids]
    print(json.dumps({
        "md5": args.md5,
        "chars": len(body),
        "ntokens": len(ids),
        "token_ids": ids[:args.limit],
        "decoded_pieces": pieces[:args.limit],
        "note": f"showing first {args.limit} tokens; use --limit 0 for all ids (no decode)",
    }, indent=1, ensure_ascii=False))
    if args.show:
        print("---BODY-BEGIN---")
        print(body)
        print("---BODY-END---")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ingest")
    p.add_argument("rows_json"); p.add_argument("out_parquet")
    p.add_argument("--body-col", default="body")
    p = sub.add_parser("census")
    p.add_argument("parquet"); p.add_argument("--top", type=int, default=25)
    p = sub.add_parser("tokens")
    p.add_argument("parquet"); p.add_argument("--md5", required=True)
    p.add_argument("--body-col", default="body")
    p.add_argument("--limit", type=int, default=64)
    p.add_argument("--show", action="store_true")
    args = ap.parse_args()
    {"ingest": cmd_ingest, "census": cmd_census, "tokens": cmd_tokens}[args.cmd](args)


if __name__ == "__main__":
    main()
