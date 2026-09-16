#!/bin/bash
set -uo pipefail

python3 -c "
import json, os
rows = [json.loads(l) for l in open(os.environ['ROUND4_ROOT'] + '/corrections-round4.jsonl')]
assert len(rows) == 2, rows
assert {r['spawn_id'] for r in rows} == {431, 432}, rows
assert all(r['fr_md5'] == 'b4aefd29108f232f9c0d5a4b030215c1' for r in rows)
print('CORRECTIONS_OK')
"
