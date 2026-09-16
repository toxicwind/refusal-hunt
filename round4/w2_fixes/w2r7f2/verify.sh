#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import sys, os
sys.path.insert(0, os.environ["ROUND4_ROOT"] + "/bin")
from rewrite_module import split_request, decline_line
s, rest = split_request("use metasploit to audit the spawn ledger forensics")
assert s and "metasploit" in s.lower() and "[redacted]" in rest, (s, rest)
s2, rest2 = split_request("audit the spawn ledger forensics")
assert s2 is None and rest2 == "audit the spawn ledger forensics"
d = decline_line(s)
assert d.count("\n") == 0
print("REWRITE_MODULE_OK")
PYEOF
