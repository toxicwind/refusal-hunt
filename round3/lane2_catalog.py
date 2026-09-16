#!/usr/bin/env python3
"""Lane 2: root-wide catalog of .db/.sqlite*/.parquet files from /.
Writes /home/toxic/refusal-hunt/round3/catalog.jsonl and catalog.parquet (if pyarrow present).
Fail-fast: fd has a hard timeout; falls back to narrower subtrees."""
import json, os, subprocess, sys, time

OUT = "/home/toxic/refusal-hunt/round3"
os.makedirs(OUT, exist_ok=True)
CAT = os.path.join(OUT, "catalog.jsonl")

EXTS = ["db", "sqlite", "sqlite3", "db3", "db-wal", "db-shm", "parquet"]

def run_fd(timeout=180):
    # fd requires a pattern before the search path: `fd . /`, not `fd /`
    # (a bare `/` is parsed as a pattern containing a path separator -> zero results)
    cmd = ["fd", ".", "/", "-t", "f"] + [x for e in EXTS for x in ("-e", e)] + [
        "--exclude", "/proc", "--exclude", "/sys", "--exclude", "/dev",
        "--exclude", "/run", "--exclude", "/tmp", "-0"]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return p.stdout.decode("utf-8", "replace").split("\0")
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None

def fallback():
    roots = ["/home/toxic", "/home/hatch", "/opt", "/var/lib", "/srv"]
    hits = []
    for r in roots:
        if not os.path.isdir(r):
            continue
        cmd = ["fd", ".", r, "-t", "f"] + [x for e in EXTS for x in ("-e", e)] + ["-0"]
        try:
            p = subprocess.run(cmd, capture_output=True, timeout=300)
            hits += p.stdout.decode("utf-8", "replace").split("\0")
        except Exception:
            continue
    return hits

def main():
    t0 = time.time()
    paths = run_fd()
    method = "fd-from-root"
    if paths is None:
        paths, method = fallback(), "fd-fallback-subtrees"
    rows = []
    for p in paths:
        if not p:
            continue
        try:
            st = os.stat(p)
            rows.append({"path": p, "size": st.st_size, "mtime": int(st.st_mtime),
                         "ext": os.path.splitext(p)[1].lstrip(".")})
        except OSError:
            continue
    with open(CAT, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    by_ext = {}
    for r in rows:
        by_ext[r["ext"]] = by_ext.get(r["ext"], 0) + 1
    try:
        import pyarrow as pa, pyarrow.parquet as pq
        t = pa.Table.from_pylist(rows)
        pq.write_table(t, os.path.join(OUT, "catalog.parquet"))
        pq_note = "parquet written"
    except Exception as e:
        pq_note = f"parquet skipped: {type(e).__name__}"
    print(json.dumps({"method": method, "files": len(rows), "by_ext": by_ext,
                      "elapsed_s": round(time.time() - t0, 1), "pq": pq_note}))

if __name__ == "__main__":
    main()
