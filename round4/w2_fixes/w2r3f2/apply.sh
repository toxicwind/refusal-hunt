#!/bin/bash
set -uo pipefail

mkdir -p "$HOME/bin" "$HOME/dl"
curl -sfL -m 120 -o "$HOME/dl/gron.tgz" "https://github.com/tomnomnom/gron/releases/download/v0.7.1/gron-linux-amd64-0.7.1.tgz" || exit 1
tar -xzf "$HOME/dl/gron.tgz" -C "$HOME/dl" --no-same-owner || exit 1
cp "$HOME/dl/gron" "$HOME/bin/gron" && chmod +x "$HOME/bin/gron"
echo "gron installed"
