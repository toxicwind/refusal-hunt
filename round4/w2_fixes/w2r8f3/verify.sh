#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_summary.json"))
assert d["fixes"] == 24, d  # 24 distinct wave-2 fix ids; reruns supersede (latest row wins)
assert len(d["by_round"]) == 8, d
print("WAVE2_SUMMARY_OK", d["totals"])
PYEOF
