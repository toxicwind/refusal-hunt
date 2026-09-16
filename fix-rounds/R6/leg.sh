#!/usr/bin/env bash
# synthetic fix-shaped leg: snapshot file, hash it 300x (cpu), verify, cleanup
f=$(mktemp /tmp/raceleg.XXXXXX) || exit 2
echo payload > "$f"
for i in $(seq 1 300); do sha256sum "$f" >/dev/null || exit 3; done
echo ok > "$f"; test "$(cat "$f")" = ok; rc=$?
rm -f "$f"; exit $rc
