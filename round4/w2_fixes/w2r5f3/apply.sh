#!/bin/bash
set -uo pipefail

lsns > "$ROUND4_ROOT/rounds/w2_lsns.txt" 2>&1
ip netns list > "$ROUND4_ROOT/rounds/w2_netns.txt" 2>&1 || echo "no iproute2 netns" > "$ROUND4_ROOT/rounds/w2_netns.txt"
echo "namespaces inventoried"
