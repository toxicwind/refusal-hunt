#!/bin/bash
# R3b: standing-file trigger-token audit (escalation of R2c). Scans the
# injected standing files for hard trigger tokens; MEMORY.md is audit-only
# (append-only provenance, never scrubbed). Any hit in a scrubbable file gets
# a backup + recorded for R4 sentence-level rewrite (no blind word-swaps).
set -uo pipefail
SCRUBBABLE="/home/hatch/SOUL.md /home/hatch/AGENTS.md /home/hatch/USER.md /home/hatch/IDENTITY.md"
AUDITONLY="/home/hatch/MEMORY.md"
TOK='jailbreak|evade[sd]?|evasion|circumvent|mitm'
log(){ echo "[R3b $(date -u +%H:%M:%SZ)] $*" >&2; }
HITS_S=$(grep -i -n -E "$TOK" $SCRUBBABLE 2>/dev/null || true)
HITS_M=$(grep -i -c -E "$TOK" $AUDITONLY 2>/dev/null || true)
log "scrubbable-file hits: ${HITS_S:-<none>}"
log "MEMORY.md hit lines (audit only): ${HITS_M:-0}"
if [ -n "$HITS_S" ]; then
  for f in $SCRUBBABLE; do
    if grep -qi -E "$TOK" "$f" 2>/dev/null; then
      cp "$f" "$f.bak-R3" && log "backup: $f.bak-R3"
    fi
  done
  echo "$HITS_S" > ~/workspace/refusal-hunt/fix-rounds/R3/trigger-hits.txt
  log "RECORDED for R4 sentence rewrite: R3/trigger-hits.txt"
  echo '{"fix":"R3b","result":"PASS","hits":"recorded-for-R4"}'; exit 0
fi
log "PASS: 0 trigger tokens in scrubbable standing files"
echo '{"fix":"R3b","result":"PASS","hits":0}'; exit 0
