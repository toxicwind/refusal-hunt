#!/bin/bash
# R4a: R3a retry — remote atomic backup + integrity verify, with the nested
# $(...) properly escaped (\$(...)) so the LOCAL shell does not execute the
# remote substitutions (R3a's root cause: local `wc -c < /home/toxic/...`
# failed, remote echo printed blanks).
set -uo pipefail
BRIDGE=~/workspace/skills/awrawr-mcp/bin/exec.py
URBIN=/home/toxic/bin/ur
D=/home/toxic/.shingle/directives.md
BAK=/home/toxic/.shingle/directives.md.bak-R2a
BASELINE=143924
log(){ echo "[R4a $(date -u +%H:%M:%SZ)] $*" >&2; }
OUT=$(python3 "$BRIDGE" --timeout 30 --argv sh -c "$URBIN sh -c 'cp -p $D $BAK && echo \"\$(wc -c < $D) \$(wc -c < $BAK) \$(grep -c MARKER:REFUSAL-BACKOFF $D)\"'" 2>/dev/null | tr -d ' \n' || true)
log "remote reports: ${OUT:-<unparseable>}"
SZ_D=$(echo "$OUT" | awk '{print $1}'); SZ_B=$(echo "$OUT" | awk '{print $2}'); MC=$(echo "$OUT" | awk '{print $3}')
if [ -n "$SZ_D" ] && [ "$SZ_D" = "$SZ_B" ] && [ "${MC:-0}" -ge 1 ] 2>/dev/null && [ "$SZ_D" -gt "$BASELINE" ] 2>/dev/null; then
  log "PASS: backup=$BAK size=$SZ_D marker=$MC (baseline $BASELINE)"
  echo "{\"fix\":\"R4a\",\"result\":\"PASS\",\"size\":$SZ_D,\"marker\":$MC}"; exit 0
else
  log "FAIL: size_d=${SZ_D:-?} size_bak=${SZ_B:-?} marker=${MC:-?}"
  echo '{"fix":"R4a","result":"FAIL","reason":"integrity"}'; exit 1
fi
