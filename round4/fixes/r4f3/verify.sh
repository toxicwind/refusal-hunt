#!/bin/bash
set -uo pipefail

python3 -c "
import json, os
d = json.load(open(os.environ['ROUND4_ROOT'] + '/rounds/r4_sleep_audit.json'))
assert isinstance(d, dict)
print('SLEEP_AUDIT_OK')
"
