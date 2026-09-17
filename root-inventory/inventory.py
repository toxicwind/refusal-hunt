#!/usr/bin/env python3
"""Root-seeded filesystem inventory. Read-only. Writes parquet."""
import os, sys, stat, hashlib, datetime
import pyarrow as pa
import pyarrow.parquet as pq

OUTDIR = os.path.expanduser("~/workspace/refusal-hunt/root-inventory")
os.makedirs(OUTDIR, exist_ok=True)

# Trees to inventory recursively; virtual filesystems excluded outright.
TREES = ["/root", "/opt", "/etc", "/usr/local", "/var", "/home"]
EXCLUDE_PREFIXES = ("/proc", "/sys", "/dev", "/run", "/tmp/.", )
TOP_LEVEL = True  # also record depth-1 entries of /

rows = []
def add(path, st):
    name = os.path.basename(path)
    rows.append({
        "path": path,
        "name": name,
        "is_hidden": name.startswith("."),
        "is_dir": stat.S_ISDIR(st.st_mode),
        "is_symlink": os.path.islink(path),
        "size": st.st_size,
        "mtime_utc": datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat(),
        "mode": oct(stat.S_IMODE(st.st_mode)),
        "uid": st.st_uid,
        "gid": st.st_gid,
        "depth": path.rstrip("/").count("/"),
        "sha256": "",
    })

def sha_small(path, st):
    if stat.S_ISREG(st.st_mode) and st.st_size <= 1_000_000:
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                h.update(f.read())
            return h.hexdigest()
        except OSError:
            return ""
    return ""

def excluded(path):
    return path.startswith(EXCLUDE_PREFIXES)

if TOP_LEVEL:
    try:
        for name in sorted(os.listdir("/")):
            p = "/" + name
            try:
                add(p, os.lstat(p))
            except OSError:
                pass
    except OSError as e:
        print("top-level list failed:", e, file=sys.stderr)

for tree in TREES:
    for dirpath, dirnames, filenames in os.walk(tree, followlinks=False):
        # prune excluded / virtual dirs in place
        dirnames[:] = [d for d in dirnames
                       if not excluded(os.path.join(dirpath, d))]
        if excluded(dirpath):
            dirnames[:] = []
            continue
        try:
            add(dirpath, os.lstat(dirpath))
        except OSError:
            pass
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if excluded(p):
                continue
            try:
                st = os.lstat(p)
            except OSError:
                continue
            add(p, st)
            if rows and not rows[-1]["is_dir"]:
                rows[-1]["sha256"] = sha_small(p, st)

ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
out = os.path.join(OUTDIR, f"inventory-{ts}.parquet")
table = pa.Table.from_pylist(rows)
pq.write_table(table, out, compression="zstd")
print(f"wrote {len(rows)} rows -> {out}")
