#!/bin/bash
# R5c: `br` — quoting-safe awrawr-pc bridge runner. Centralizes the exec.py
# invocation pattern that R3a/R4a got wrong (nested $(...) evaluated locally).
# Contract: pass the remote script as ONE single-quoted arg; br never evals
# locally. Avoid single-quotes inside the script. Self-test covers the exact
# R4a hard case (nested $() evaluated on the REMOTE side).
set -uo pipefail
BR=~/workspace/bin/br
log(){ echo "[R5c $(date -u +%H:%M:%SZ)] $*" >&2; }
cat > "$BR" <<'BREOF'
#!/bin/bash
# br '<remote sh script>' — run on awrawr-pc via the exec bridge.
# Prints raw remote stdout; exit code = bridge exit code. Never evals locally.
set -uo pipefail
SCRIPT="${1:-}"
[ -n "$SCRIPT" ] || { echo "br: usage: br '<remote sh script>'" >&2; exit 2; }
exec python3 "$HOME/workspace/skills/awrawr-mcp/bin/exec.py" --timeout 60 \
  --argv sh -c "/home/toxic/bin/ur sh -c '$SCRIPT'"
BREOF
chmod +x "$BR"
T1=$("$BR" 'echo hello-remote' 2>/dev/null | tr -d '\n')
[ "$T1" = "hello-remote" ] || { log "selftest1 FAIL: [$T1]"; exit 1; }
T2=$("$BR" 'echo "words=$(echo a b c | wc -w)"' 2>/dev/null | tr -d '\n')
[ "$T2" = "words=3" ] || { log "selftest2 FAIL: [$T2]"; exit 1; }
log "PASS: br installed; nested remote \$() proven (words=3)"
echo '{"fix":"R5c","result":"PASS"}'; exit 0
