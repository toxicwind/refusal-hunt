#!/bin/bash
set -uo pipefail

python3 - <<"PYEOF"
import json, os
R = os.environ["ROUND4_ROOT"]
gate = json.load(open(R + "/rounds/r2_gate.json"))
COVERAGE = {
    "squawk-ws-client-watchdog": "cell supervisor watchdog-supervisor.sh section 1",
    "service-restart-watchdog": "cell supervisor watchdog-supervisor.sh section 1",
    "fleet-snapshot-5m": "NONE - accepted risk (no gate-proof cover)",
    "whatsapp-fleet-digest": "NONE - accepted risk (no gate-proof cover)",
}
out = {}
for job, d in gate["per_job"].items():
    cov = COVERAGE.get(job, "NONE - poller itself or uncovered; degraded until gate clears")
    out[job] = {"skipped_n": d["skipped"], "total_n": d["n"], "covered_by": cov,
                "risk": "covered" if not cov.startswith("NONE") else "accepted"}
json.dump(out, open(R + "/rounds/r4_coverage.json", "w"), indent=1)
print("coverage jobs=%d uncovered=%d" % (len(out), sum(1 for v in out.values() if v["risk"] == "accepted")))
PYEOF
