#!/bin/bash
set -uo pipefail

python3 -c "
import json, os
d = json.load(open(os.environ['ROUND4_ROOT'] + '/rounds/r6_dbsweep.json'))
assert d['count'] > 0, d
print('DBSWEEP_OK', d['count'])
"
