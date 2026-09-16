#!/bin/bash
set -uo pipefail

mkdir -p "$HOME/bin"
cat > "$HOME/bin/pkill-guard" <<'SHEOF'
#!/bin/bash
# pkill-guard v2: never pkill a pattern matching your own process chain.
# Structural fix for the 2026-09-16 pkill -f footgun (killed own supervisor).
dry=0
[ "${1:-}" = "--dry-run" ] && { dry=1; shift; }
pat="${1:?usage: pkill-guard [--dry-run] <pattern> [pkill args...]}"; shift
src="${BASH_SOURCE[0]}"
case "$src" in *"$pat"*) echo "REFUSED: pattern matches guard's own path ($src)" >&2; exit 3;; esac
pid=$(awk '{print $4}' "/proc/$$/stat" 2>/dev/null); [ -z "$pid" ] && pid=1
while [ "$pid" -gt 1 ]; do
  cmd=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null)
  case "$cmd" in *"$pat"*) echo "REFUSED: pattern '$pat' matches ancestor pid=$pid" >&2; exit 3;; esac
  pid=$(awk '{print $4}' "/proc/$pid/stat" 2>/dev/null); [ -z "$pid" ] && pid=1
done
[ "$dry" = 1 ] && { echo "WOULD-PKILL: $pat"; exit 0; }
exec pkill "$pat" "$@"
SHEOF
chmod +x "$HOME/bin/pkill-guard"
echo "guard v2 installed"
