#!/bin/bash
set -uo pipefail

python3 -c "
import sys, os
sys.path.insert(0, os.environ['ROUND4_ROOT'] + '/rounds')
from refusal_classifier import classify
assert classify('pong') == 'pong_genuine'
assert classify(None) == 'no_response'
assert classify('hello world') == 'unknown'
print('CLASSIFIER_OK')
"
