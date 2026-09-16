#!/bin/bash
set -uo pipefail

bash -n "$HOME/workspace/watchdog-supervisor.sh" || exit 1
grep -q "R4-STAGING" "$HOME/workspace/watchdog-supervisor.sh" || exit 2
pgrep -f "[w]atchdog-supervisor.sh" >/dev/null || exit 3
echo STAGE_PATCH_OK
