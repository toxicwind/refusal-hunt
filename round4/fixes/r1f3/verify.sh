#!/bin/bash
set -uo pipefail

out=$("$ROUND4_ROOT/bin/tmp-guard.sh" 2>&1); rc=$?
echo "$out" | grep -q "tmp_usage_pct=" || exit 1
echo "TMP_GUARD_OK rc=$rc"
