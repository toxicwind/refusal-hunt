#!/bin/bash
set -uo pipefail

python3 -c "
import json, os
d = json.load(open(os.environ['ROUND4_ROOT'] + '/rounds/r5_chain.json'))
bad = [k for k, v in d.items() if not v['exists']]
assert not bad, bad
print('CHAIN_OK', len(d))
"
