#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
gate = json.load(open(R + "/rounds/w2_gate.json"))["per_job"]
cov = json.load(open(R + "/rounds/w2_coverage.json"))
assert set(cov) == set(gate), "job set mismatch"
assert all(v.get("covered_by") for v in cov.values())
print("COVERAGE_V2_OK", len(cov))
PYEOF
