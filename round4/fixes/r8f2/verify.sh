#!/bin/bash
set -uo pipefail

[ -s "$ROUND4_ROOT/dashboard.html" ] || exit 1
grep -q "r8f1" "$ROUND4_ROOT/dashboard.html" || exit 2
echo DASHBOARD_OK
