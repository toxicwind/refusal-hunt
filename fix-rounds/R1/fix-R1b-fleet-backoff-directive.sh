#!/bin/bash
# fix-R1b-fleet-backoff-directive.sh — append the refusal-backoff directive to
# the fleet channel (/home/toxic/.shingle/directives.md, newest-at-bottom).
# Rollback: restore the pre-round snapshot directives.md.bak-R1.
set -uo pipefail
BRIDGE=/home/hatch/workspace/skills/awrawr-mcp/bin/exec.py
XFER=/home/hatch/workspace/skills/awrawr-mcp/bin/xfer.py
D=/home/toxic/.shingle/directives.md
BAK=/home/toxic/.shingle/directives.md.bak-R1
URBIN=/home/toxic/bin/ur
BLOCK_LOCAL=/home/hatch/workspace/refusal-hunt/fix-rounds/R1/backoff-block.md
BLOCK_REMOTE=/home/toxic/refusal-hunt/fix-rounds/R1-backoff-block.md
log(){ echo "[R1b $(date -u +%FT%TZ)] $*" >&2; }
rollback(){ log "ROLLBACK: restoring $D"; $URBIN cp "$BAK" "$D" 2>/dev/null || python3 "$BRIDGE" --timeout 25 --argv cp "$BAK" "$D" >/dev/null 2>&1; log "rollback done"; }
rstdout(){
  python3 "$BRIDGE" --timeout 25 --argv sh -c "$1" 2>/dev/null \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("stdout",""))' 2>/dev/null
}

[ -f "$BLOCK_LOCAL" ] || { log "ABORT: block file missing"; exit 2; }
python3 "$XFER" put "$BLOCK_LOCAL" "$BLOCK_REMOTE" >/dev/null 2>&1 || { log "xfer failed"; exit 1; }
OUT=$(rstdout "$URBIN sh -c 'if grep -q \"MARKER:REFUSAL-BACKOFF\" $D; then echo RESULT=PRESENT; else cat $BLOCK_REMOTE >> $D && echo RESULT=APPENDED; fi'")
RES=$(echo "$OUT" | grep -o 'RESULT=[A-Z]*' | head -1)
log "remote reports: ${RES:-unparseable}"
if [ "$RES" = "RESULT=PRESENT" ] || [ "$RES" = "RESULT=APPENDED" ]; then
  echo "PASS R1b ($RES)"; exit 0
fi
# Ambiguous: re-check ground truth before deciding.
CNT=$(rstdout "$URBIN grep -c \"MARKER:REFUSAL-BACKOFF\" $D" | tail -1)
if [ "$CNT" -ge 1 ] 2>/dev/null; then log "recheck: marker present ($CNT)"; echo "PASS R1b (recheck)"; exit 0; fi
log "VERIFY FAIL: marker absent after append"; rollback; exit 1
