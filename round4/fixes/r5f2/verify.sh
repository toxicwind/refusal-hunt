#!/bin/bash
set -uo pipefail

python3 -c "
import json, os
d = json.load(open(os.environ['ROUND4_ROOT'] + '/rounds/r5_feed.json'))
assert d['landed'] is True, d
print('FEED_OK', d)
"
