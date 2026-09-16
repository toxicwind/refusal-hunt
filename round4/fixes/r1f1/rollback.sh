#!/bin/bash
set -uo pipefail

MARK="$HOME/.local/.r4_nest_installed"
if [ -f "$MARK" ]; then pip uninstall -y -q nest_asyncio; rm -f "$MARK"; echo "uninstalled"; else echo "not ours, kept"; fi
