#!/bin/bash
set -uo pipefail

MARK="$HOME/.local/.r4_nest_installed"
python3 -c "import nest_asyncio" 2>/dev/null || {
  pip install --user --break-system-packages -q nest_asyncio && touch "$MARK" && echo "installed nest_asyncio"
}
echo "apply done"
