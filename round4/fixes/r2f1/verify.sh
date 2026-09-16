#!/bin/bash
set -uo pipefail

python3 -c "
import json, os
d = json.load(open(os.environ['ROUND4_ROOT'] + '/rounds/r2_storm.json'))
assert d['overall_rate'] > 0.40, d
assert d['n'] >= 100, d
print('STORM_QUANT_OK', d['overall_rate'])
"
