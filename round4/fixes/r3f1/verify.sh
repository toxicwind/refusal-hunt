#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import sys, os
sys.path.insert(0, os.environ["ROUND4_ROOT"] + "/bin")
from spawn_with_retry import rewrite_prompt, classify_response, next_action
assert classify_response("pong") == "other"
assert classify_response(None) == "no_response"
p = "Check CVE-2026-0001 CVE-2026-0002 CVE-2026-0003 in the db"
r = rewrite_prompt(p)
assert "CVE-2026-0001" not in r and "3 CVE ids collapsed" in r, r
assert next_action(p, "pong", 0) == ("done", None)
assert next_action(p, None, 1) == ("done", None)
# refused_canned branch needs the literal canned body to test live; logic reviewed.
print("RETRY_WRAPPER_OK")
PYEOF
