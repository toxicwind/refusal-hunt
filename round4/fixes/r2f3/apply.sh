#!/bin/bash
set -uo pipefail

cat > "$ROUND4_ROOT/rounds/refusal_classifier.py" <<'PYEOF'
"""md5-identity refusal classifier. Never stores refusal plaintext (hash only)."""
import hashlib
SIGS = {
    "refused_canned_spawn": "b4aefd29108f232f9c0d5a4b030215c1",
    "refused_canned_chat": "582bcbd080daeb3f826c45ed4a83b265",
    "pong_genuine": "6fdb087aa3fbfbcb8287a593a0919e61",
}
INV = {v: k for k, v in SIGS.items()}
def classify(body):
    if body is None:
        return "no_response"
    return INV.get(hashlib.md5(body.encode()).hexdigest(), "unknown")
PYEOF
python3 -c "
import json, os
R = os.environ['ROUND4_ROOT']
consts = json.load(open(R + '/input/constants.json'))['md5']
json.dump({'spawn_canned': consts['spawn_canned_refusal'],
           'chat_canned': consts['chat_canned_refusal'],
           'pong': consts['pong_genuine'],
           'note': 'hash identity only; plaintext never stored'}, open(R + '/rounds/r2_sigs.json','w'), indent=1)
print('sigs written')
"
