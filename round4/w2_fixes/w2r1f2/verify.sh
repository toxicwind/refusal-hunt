#!/bin/bash
set -uo pipefail

G="$HOME/bin/pkill-guard"
[ -x "$G" ] || exit 1
ln -sf "$G" /tmp/w2-watchdog-supervisor.sh
/tmp/w2-watchdog-supervisor.sh --dry-run "watchdog-supervisor" >/dev/null 2>&1; rc1=$?
"$G" --dry-run "zzz-no-such-proc-99999" >/dev/null 2>&1; rc2=$?
printf '#!/bin/bash\n"$HOME/bin/pkill-guard" --dry-run "ancestor-probe" >/dev/null 2>&1\necho "rc=$?"\n' > /tmp/w2-ancestor-probe.sh
chmod +x /tmp/w2-ancestor-probe.sh
rc3=$(/tmp/w2-ancestor-probe.sh | sed 's/rc=//')
rm -f /tmp/w2-watchdog-supervisor.sh /tmp/w2-ancestor-probe.sh
[ "$rc1" = "3" ] || { echo "self-path not refused rc=$rc1"; exit 1; }
[ "$rc2" = "0" ] || { echo "negative failed rc=$rc2"; exit 1; }
[ "$rc3" = "3" ] || { echo "ancestor not refused rc=$rc3"; exit 1; }
echo PKILL_GUARD_V2_OK
