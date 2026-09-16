#!/bin/bash
set -uo pipefail

python3 -c "
import json, os
d = json.load(open(os.environ['ROUND4_ROOT'] + '/rounds/r4_gate_timeline.json'))
assert d['continuous_skip'] is True, d
assert d['duration_h'] > 1, d
print('TIMELINE_OK', d['duration_h'], 'h continuous')
"
