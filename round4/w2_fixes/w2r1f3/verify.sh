#!/bin/bash
set -uo pipefail
grep -q "^- round8:" "$ROUND4_ROOT/ROUNDS_SUMMARY.md" || exit 1; echo RUNBOOK_REPAIR_OK