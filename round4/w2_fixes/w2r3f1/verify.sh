#!/bin/bash
set -uo pipefail

"$HOME/sdk/go/bin/go" version || exit 1
echo GO_TOOLCHAIN_RACE_OK
