#!/bin/bash
set -uo pipefail

G="$HOME/bin/pkill-guard"
[ -x "$G" ] || exit 1
bash -c 'exec -a "watchdog-supervisor.sh" bash -c "\"$0\" --dry-run \"watchdog-supervisor.sh\""' "$G" 2>/dev/null
rc1=$?
"$G" --dry-run "zzz-no-such-proc-12345" >/dev/null 2>&1
rc2=$?
[ "$rc1" = "3" ] && [ "$rc2" = "0" ] || { echo "rc1=$rc1 rc2=$rc2"; exit 1; }
echo PKILL_GUARD_OK
