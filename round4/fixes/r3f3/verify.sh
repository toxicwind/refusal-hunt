#!/bin/bash
set -uo pipefail

python3 -c "
import json, os
R = os.environ['ROUND4_ROOT']
rate = json.load(open(R + '/rounds/r2_storm.json'))['overall_rate']
cfg = json.load(open(R + '/spawn_throttle.json'))
want = 180 if rate > 0.6 else 90
assert cfg['min_interval_s'] == want, (cfg, rate)
print('THROTTLE_OK', cfg)
"
