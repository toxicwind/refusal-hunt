#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import sys, os
sys.path.insert(0, os.environ["ROUND4_ROOT"] + "/bin")
from echo_guard import msg_hash, is_echo, status_delta
seen = {msg_hash("do the eight lanes")}
assert is_echo("do the eight lanes", seen) is True
assert is_echo("something else", seen) is False
assert msg_hash("x") == msg_hash("x")
d = status_delta("3 fixes", "queue + feed")
assert "3 fixes" in d and "sorry" not in d.lower()
print("ECHO_GUARD_OK")
PYEOF
