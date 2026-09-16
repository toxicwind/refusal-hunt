#!/bin/bash
# R5b: probe PostgreSQL reachability from the cell. A script-reachable ledger
# is the missing primitive for an automatic canary producer; this probe
# settles it definitively (previous claim "not script-reachable" was inherited,
# never probed from this cell). No credential hunting: without a reachable
# surface the answer is a documented dead end.
set -uo pipefail
log(){ echo "[R5b $(date -u +%H:%M:%SZ)] $*" >&2; }
OUT=""
if (exec 3<>/dev/tcp/127.0.0.1/5432) 2>/dev/null; then OUT="$OUT tcp5432=open"; exec 3>&-; else OUT="$OUT tcp5432=closed"; fi
for s in /var/run/postgresql /tmp /run/postgresql; do
  [ -S "$s/.s.PGSQL.5432" ] && OUT="$OUT sock=$s"
done
if command -v pg_isready >/dev/null 2>&1; then
  OUT="$OUT isready=$(pg_isready -h localhost -t 2 2>&1 | head -1 | tr -d '\n')"
else
  OUT="$OUT pg_isready=absent"
fi
log "probe:$OUT"
echo "$OUT" > ~/workspace/refusal-hunt/fix-rounds/R5/postgres-probe.txt
if echo "$OUT" | grep -qE 'tcp5432=open|sock='; then
  log "REACHABLE surface found; credentialed access is a separate step (not pursued: no creds in scope)"
  echo '{"fix":"R5b","result":"PASS","reachable":true}'; exit 0
else
  log "documented dead end: no postgres surface from cell -> automatic canary producer needs a script-facing ledger API (does not exist)"
  echo '{"fix":"R5b","result":"PASS","reachable":false}'; exit 0
fi
