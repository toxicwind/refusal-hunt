#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os, shutil, subprocess
R = os.environ["ROUND4_ROOT"]
tools = {}
for t in ["fdfind", "fd", "rg", "python3", "node", "ctags", "tree"]:
    p = shutil.which(t)
    ver = ""
    if p:
        try:
            r = subprocess.run([t, "--version"], capture_output=True, text=True, timeout=10)
            blob = (r.stdout or r.stderr)
            ver = blob.splitlines()[0][:80] if blob else ""
        except Exception:
            ver = "err"
    tools[t] = {"path": p, "version": ver}
gobin = os.path.expanduser("~/sdk/go/bin/go")
tools["go_toolchain"] = {"path": gobin, "present": os.path.isfile(gobin)}
json.dump(tools, open(R + "/rounds/w2_tools.json", "w"), indent=1)
print(json.dumps(tools, indent=1))
PYEOF
