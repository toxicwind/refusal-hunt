#!/bin/bash
set -uo pipefail

python3 "$HOME/workspace/refusal-hunt/round3/spawn_guard.py" --selftest || exit 1
python3 -c "
import sys
sys.path.insert(0, '$HOME/workspace/refusal-hunt/round3')
from spawn_guard import verify_spawn_record
r = verify_spawn_record(1, 'completed', 'pong')
assert r['truth'] == 'genuine' and r['status_lied'] is False, r
r = verify_spawn_record(2, 'completed', None)
assert r['truth'] == 'no_response', r
print('GUARD_POSTVERIFY_OK')
"
