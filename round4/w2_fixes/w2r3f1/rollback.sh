#!/bin/bash
set -uo pipefail

if [ -f "$HOME/sdk/.w2_go_ver" ]; then rm -rf "$HOME/sdk/go" "$HOME/sdk/.w2_go_ver"; echo "toolchain removed"; else echo "not ours, kept"; fi
