#!/usr/bin/env python3
"""safe_write.py -- append-exception guards for cron-relied file writes.

Every writer below follows one contract:

  FAIL LOUD, KEEP THE PRIOR GOOD COPY INTACT.
  A failed write must never leave a zero-byte or truncated file behind,
  and must never report success silently.

Mechanics:
  - Full-file rewrites ("w" mode): write to a temp sibling in the SAME
    directory, flush + os.fsync, then os.replace() (atomic on POSIX).
    The old file is untouched until the instant of the rename. On any
    exception the temp file is removed and the exception RE-RAISED --
    callers see the failure, supervisors see a non-zero exit.
  - Appends ("a" mode): write the line, flush + os.fsync, verify the file
    size strictly grew, raise on any anomaly. Appends cannot be atomic,
    so a torn tail line is possible under kill -9; readers must tolerate
    a corrupt FINAL line (skip it), never a corrupt file.
  - Parquet: write temp, re-read and compare row counts, then replace.
    The prior good copy is preserved as <path>.bak before replace.

Adopted 2026-09-19 for debate 0220db63 slice 1 (cron write discipline):
the 15-min cron family must not silently produce zero-byte/missing
outputs. Prior incident: ledger/anomalies.parquet.bak-20260919-truncfix
(a truncated parquet had to be repaired from backup).
"""
import json
import os
import tempfile

__all__ = [
    "atomic_write_bytes",
    "atomic_write_text",
    "atomic_write_json",
    "append_jsonl",
    "append_text",
    "atomic_write_parquet",
]


def _tmp_in_same_dir(path):
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=d)
    return fd, tmp


def atomic_write_bytes(path, data: bytes, allow_empty: bool = False) -> int:
    """Atomically replace path with data. Returns bytes written.

    Raises on ANY failure after removing the temp file; the prior file
    is never touched unless the full payload was fsync'd to disk.
    A write that would leave a zero-byte file raises unless
    allow_empty=True -- silent truncation is exactly the failure mode
    these guards exist to prevent.
    """
    fd, tmp = _tmp_in_same_dir(path)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if os.path.getsize(tmp) == 0 and not allow_empty:
            raise OSError(f"atomic write would leave zero-byte file: {path}")
        os.replace(tmp, path)
        return len(data)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_text(path, text: str, encoding="utf-8",
                      allow_empty: bool = False) -> int:
    return atomic_write_bytes(path, text.encode(encoding),
                              allow_empty=allow_empty)


def atomic_write_json(path, obj, **dump_kw) -> int:
    dump_kw.setdefault("indent", 2)
    return atomic_write_text(path, json.dumps(obj, **dump_kw) + "\n")


def _verify_grew(path, before):
    after = os.path.getsize(path)
    if after <= before:
        raise OSError(
            f"append verification failed: {path} size {before} -> {after}, "
            f"expected strict growth")


def append_text(path, text: str, encoding="utf-8") -> int:
    """Append text with fsync + size-growth verification. Raises on failure.

    Note: under kill -9 mid-append the tail line may tear; readers must
    tolerate a corrupt FINAL line. The file itself is never truncated.
    """
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    before = os.path.getsize(path) if os.path.exists(path) else 0
    with open(path, "a", encoding=encoding) as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    _verify_grew(path, before)
    return len(text)


def append_jsonl(path, obj) -> int:
    return append_text(path, json.dumps(obj, ensure_ascii=True) + "\n")


def atomic_write_parquet(df, path, keep_backup=True, **to_parquet_kw) -> int:
    """Atomically replace a parquet file; keeps <path>.bak of prior copy.

    Writes to a temp sibling, re-reads it to verify row count matches,
    then os.replace(). The old good copy is preserved at <path>.bak
    (overwritten each successful write) so a bad replace is recoverable.
    Raises on any failure; the live path is never left zero-byte.
    """
    import pandas as pd  # local import: pyarrow/pandas only where needed

    expected = len(df)
    fd, tmp = _tmp_in_same_dir(path)
    os.close(fd)
    os.unlink(tmp)  # pandas writes the file itself; give it a clean name
    tmp = tmp + ".parquet"
    try:
        to_parquet_kw.setdefault("compression", "zstd")
        to_parquet_kw.setdefault("index", False)
        df.to_parquet(tmp, **to_parquet_kw)
        got = len(pd.read_parquet(tmp, columns=[df.columns[0]]))
        if got != expected:
            raise OSError(
                f"parquet write verification failed: wrote {expected} rows, "
                f"temp file has {got}")
        if keep_backup and os.path.exists(path):
            bak = path + ".bak"
            # copy current good file aside (read+write, no rename games
            # with the live path)
            with open(path, "rb") as src, open(bak + ".new", "wb") as dst:
                while True:
                    chunk = src.read(1 << 20)
                    if not chunk:
                        break
                    dst.write(chunk)
                dst.flush()
                os.fsync(dst.fileno())
            os.replace(bak + ".new", bak)
        # fsync the temp parquet before the atomic replace
        with open(tmp, "rb") as f:
            os.fsync(f.fileno())
        os.replace(tmp, path)
        return expected
    except BaseException:
        for p in (tmp, tmp + ".new"):
            try:
                os.unlink(p)
            except OSError:
                pass
        raise
