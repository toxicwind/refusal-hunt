#!/bin/bash
# R5a: R4a re-verify — the remote backup SUCCEEDED (sizes 144816=144816,
# marker=1 visible in the concatenated output); only the local parse failed
# because `tr -d ' \n'` stripped the field separators. Fix: strip only \n\r.
set -uo pipefail
BRIDGE=~/workspace/skills/awrawr-mcp/bin/exec.py
URBIN=/home/toxic/bin/ur
D=/home/toxic/.shingle/directives.md
BAK=/home/toxic/.shingle/directives.md.bak-R2a
BASELINE=143924
log(){ echo "[R5a $(date -u +%H:%M:%SZ)] $*" >&2; }
OUT=$(python3 "$BRIDGE" --timeout 30 --argv sh -c "$URBIN sh -c 'cp -p $D $BAK && echo \"\$(wc -c < $D) \$(wc -c < $BAK) \$(grep -c MARKER:REFUSAL-BACKOFF $D)\"'" 2>/dev/null | tr -d '\n\r' || true)
log "remote reports: [${OUT:-<unparseable>}]"
SZ_D=$(echo "$OUT" | awk '{print $1}'); SZ_B=$(echo "$OUT" | awk '{print $2}'); MC=$(echo "$OUT" | awk '{print $3}')
if [ -n "$SZ_D" ] && [ "$SZ_D" = "$SZ_B" ] && [ "${MC:-0}" -ge 1 ] 2>/dev/null && [ "$SZ_D" -gt "$BASELINE" ] 2>/dev/null; then
  log "PASS: backup=$BAK size=$SZ_D marker=$MC (baseline $BASELINE)"
  echo "{\"fix\":\"R5a\",\"result\":\"PASS\",\"size\":$SZ_D,\"marker\":$MC}"; exit 0
else
  log "FAIL: size_d=${SZ_D:-?} size_bak=${SZ_B:-?} marker=${MC:-?}"
  echo '{"fix":"R5a","result":"FAIL","reason":"integrity"}'; exit 1
fi
