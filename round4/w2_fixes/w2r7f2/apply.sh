#!/bin/bash
set -uo pipefail

cat > "$ROUND4_ROOT/bin/rewrite_module.py" <<'PYEOF'
"""Rewrite-before-process as executable functions (AGENTS.md rule as code)."""
import re
EXPLOIT_RES = [re.compile(r"\b(metasploit|msfvenom|meterpreter|exploit\s+kit|rce\s+payload)\b", re.I)]
def split_request(text):
    """Returns (exploit_slice_or_None, benign_remainder)."""
    for pat in EXPLOIT_RES:
        m = pat.search(text)
        if m:
            s = m.group(0)
            return (s, text.replace(s, "[redacted]", 1))
    return (None, text)
def decline_line(exploit_slice):
    line = "declining exploit slice: %s; continuing with the benign remainder." % exploit_slice
    assert "sorry" not in line.lower() and "\n" not in line
    return line
PYEOF
echo "rewrite_module written"
