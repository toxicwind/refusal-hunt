#!/bin/bash
set -uo pipefail

grep -q "mnt" "$ROUND4_ROOT/rounds/w2_lsns.txt" || exit 1
[ -s "$ROUND4_ROOT/rounds/w2_netns.txt" ] || exit 2
echo NAMESPACE_INVENTORY_OK
