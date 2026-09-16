#!/bin/bash
set -uo pipefail

grep -q "2026-09-16" "$ROUND4_ROOT/ROUNDS_SUMMARY.md" || exit 1
grep -q "round8" "$ROUND4_ROOT/ROUNDS_SUMMARY.md" || exit 2
echo RUNBOOK_OK
