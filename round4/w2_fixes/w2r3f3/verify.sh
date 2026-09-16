#!/bin/bash
set -uo pipefail

[ -x "$ROUND4_ROOT/bin/refscan" ] || exit 1
printf '%s\n' '{"id":1,"body":"pong"}' '{"id":2,"body":"hello world"}' '{"id":3,"body":"another body here"}' \
  | "$ROUND4_ROOT/bin/refscan" -workers 2 | python3 -c "
import json, sys, hashlib
rows = {}
for l in sys.stdin:
    l = l.strip()
    if l: rows[json.loads(l)['id']] = json.loads(l)
assert rows[1]['class'] == 'pong_genuine', rows[1]
assert rows[2]['class'] == 'unknown', rows[2]
for i, body in ((1, 'pong'), (2, 'hello world'), (3, 'another body here')):
    assert rows[i]['md5'] == hashlib.md5(body.encode()).hexdigest(), rows[i]
print('REFSCAN_V2_OK')
"
