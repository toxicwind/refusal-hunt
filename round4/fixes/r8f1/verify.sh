#!/bin/bash
set -uo pipefail

python3 -c "
import json, os
d = json.load(open(os.environ['ROUND4_ROOT'] + '/rounds/r8_acceptance.json'))
assert d['verdict'] in ('PASS', 'FAIL'), d
print('ACCEPTANCE', d['verdict'], d['success_rate'])
"
