#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import os
R = os.environ["ROUND4_ROOT"]
p = R + "/ROUNDS_SUMMARY.md"
s = open(p).read() if os.path.exists(p) else ""
if "- round8:" in s:
    print("already repaired"); raise SystemExit(0)
anchor = "Next iterations:"
assert anchor in s, "anchor missing"
s = s.replace(anchor, "- round8: pass=1 rolled_back=2 skipped=0 (283ms)\n\n" + anchor, 1)
open(p, "w").write(s)
print("wave-1 summary repaired")
PYEOF
