#!/bin/bash
set -uo pipefail

"$HOME/bin/gron" --version >/dev/null 2>&1 || exit 1
echo '{"a":1}' | "$HOME/bin/gron" | grep -q "json.a = 1" || exit 2
echo GRON_OK
