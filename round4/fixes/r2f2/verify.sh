#!/bin/bash
set -uo pipefail

python3 -c "
import json, os
d = json.load(open(os.environ['ROUND4_ROOT'] + '/rounds/r2_gate.json'))
assert d['skip_rate'] > 0.9, d
assert d['last_ts'] - d['first_ts'] > 1800, d
print('GATE_QUANT_OK', d['skip_rate'])
"
