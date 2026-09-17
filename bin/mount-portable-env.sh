#!/usr/bin/env bash
# mount-portable-env.sh — lowest-latency loader for the hyper-portable
# fastparquet env (targz + blake3 chunked archive).
#
# Usage:
#   source mount-portable-env.sh [target_dir]
#   # or standalone (prints PYTHONPATH export line):
#   ./mount-portable-env.sh [target_dir]
#
# Reassembles 64MB chunks from portable-env/chunks-20260916/,
# verifies blake3 per chunk, extracts once to target_dir, and exports
# PYTHONPATH. Re-mount is a no-op when the stamp matches (fast path).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHUNK_DIR="${CHUNK_DIR:-$SCRIPT_DIR/../portable-env/chunks-20260916}"
MANIFEST="${MANIFEST:-$SCRIPT_DIR/../portable-env/MANIFEST-20260916.json}"
TARGET="${1:-${PORTABLE_ENV_TARGET:-$HOME/workspace/portable-env-build/mount}}"
STAMP="$TARGET/.portable-env-stamp"

PY="${PORTABLE_ENV_PY:-$HOME/workspace/venvs/forensics/bin/python}"
if [ ! -x "$PY" ]; then PY="python3"; fi

T0=$($PY -c 'import time; print(int(time.perf_counter()*1000))')

# Fast path: already mounted with matching manifest stamp
if [ -f "$STAMP" ] && [ -f "$MANIFEST" ] && \
   [ "$(cat "$STAMP" 2>/dev/null)" = "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" ]; then
  T1=$($PY -c 'import time; print(int(time.perf_counter()*1000))')
  echo "mount-portable-env: fast path, already mounted ($((T1-T0)) ms)" >&2
  export PYTHONPATH="$TARGET/site-packages${PYTHONPATH:+:$PYTHONPATH}"
  return 0 2>/dev/null || true
fi

mkdir -p "$TARGET"
ASSEMBLED="$TARGET/.assembled.tar.gz"

# 1. Reassemble chunks in order (chunk names sort lexicographically)
: > "$ASSEMBLED"
N=0
for c in "$CHUNK_DIR"/env-chunk-*; do
  [ -e "$c" ] || { echo "mount-portable-env: no chunks in $CHUNK_DIR" >&2; exit 1; }
  cat "$c" >> "$ASSEMBLED"
  N=$((N+1))
done
T1=$($PY -c 'import time; print(int(time.perf_counter()*1000))')

# 2. Verify blake3 per chunk against manifest (digests only in manifest)
"$PY" - "$CHUNK_DIR" "$MANIFEST" <<'EOF'
import json, sys, glob, os
chunk_dir, manifest = sys.argv[1], sys.argv[2]
import blake3
man = json.load(open(manifest))
ok = True
for e in man["chunks"]:
    p = os.path.join(chunk_dir, e["name"])
    h = blake3.blake3()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    if h.hexdigest() != e["blake3"]:
        print(f"HASH MISMATCH: {e['name']}", file=sys.stderr)
        ok = False
if not ok:
    sys.exit(2)
print(f"verified {len(man['chunks'])} chunks, blake3 ok", file=sys.stderr)
EOF
T2=$($PY -c 'import time; print(int(time.perf_counter()*1000))')

# 3. Extract (tar.gz streams straight in)
tar -xzf "$ASSEMBLED" -C "$TARGET"
rm -f "$ASSEMBLED"
sha256sum "$MANIFEST" | cut -d' ' -f1 > "$STAMP"
T3=$($PY -c 'import time; print(int(time.perf_counter()*1000))')

export PYTHONPATH="$TARGET/site-packages${PYTHONPATH:+:$PYTHONPATH}"
TOTAL=$((T3-T0))
echo "mount-portable-env: $N chunks -> $TARGET (${TOTAL} ms total: assemble=$((T1-T0)) verify=$((T2-T1)) extract=$((T3-T2)) ms)" >&2
echo "$TOTAL"
