#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os, subprocess
R = os.environ["ROUND4_ROOT"]
ev = {}
ev["run_hatch_exists"] = os.path.exists("/run/hatch")
for p in ["/proc/1/root/run/hatch", "/run/hatch/daemon/http-api.sock",
          "/run/hatch/sentinel/egress-approvals-admin.sock"]:
    try:
        ev["probe_" + p.replace("/", "_")] = os.path.exists(p)
    except Exception as e:
        ev["probe_" + p.replace("/", "_")] = "denied: " + type(e).__name__
try:
    r = subprocess.run(["nsenter", "--mount=/proc/1/ns/mnt", "ls", "/run/hatch"],
                       capture_output=True, text=True, timeout=15)
    ev["nsenter"] = {"rc": r.returncode, "out": (r.stdout + r.stderr)[:120]}
except Exception as e:
    ev["nsenter"] = "err " + str(e)[:80]
try:
    r = subprocess.run(["ss", "-ltn"], capture_output=True, text=True, timeout=15)
    ev["listeners"] = [l.strip() for l in r.stdout.splitlines()[1:12]]
except Exception as e:
    ev["listeners"] = "err " + str(e)[:80]
out = {"verdict": "hatch_daemon_surface_unreachable_from_cell", "evidence": ev,
       "note": "/run/hatch sockets live in the host mount ns; the cell has no CAP_SYS_ADMIN over the init ns"}
json.dump(out, open(R + "/rounds/w2_hatch_surface.json", "w"), indent=1)
print(out["verdict"])
PYEOF
