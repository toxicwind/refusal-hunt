#!/bin/bash
set -uo pipefail

mkdir -p "$HOME/sdk" "$HOME/go-dl"
VER=$(curl -s -m 20 "https://go.dev/dl/?mode=json" | python3 -c "import json,sys; print([v['version'] for v in json.load(sys.stdin) if v.get('stable')][0])")
[ -n "$VER" ] || { echo "no stable version"; exit 1; }
TARBALL="$HOME/go-dl/${VER}.linux-amd64.tar.gz"
[ -f "$TARBALL" ] || curl -s -m 180 -o "$TARBALL" "https://go.dev/dl/${VER}.linux-amd64.tar.gz"
[ -s "$TARBALL" ] || { echo "tarball empty"; exit 1; }
tar -xzf "$TARBALL" -C "$HOME/sdk"
echo "$VER" > "$HOME/sdk/.r4_go_ver"
echo "GO_FETCHED $VER"
