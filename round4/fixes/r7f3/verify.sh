#!/bin/bash
set -uo pipefail

python3 -c "
import json, os
d = json.load(open(os.environ['ROUND4_ROOT'] + '/rounds/r7_race.json'))
assert d['classes_agree'] is True, d
assert d['speedup'] > 1.5, d
print('RACE_OK speedup=%.2f' % d['speedup'])
"
