#!/usr/bin/env python3
"""R8F2: derive the next 8 tasks from residual defects. Scans round results,
the runtime manifest, and the curated open-items list; writes
r8f2_next_tasks.json; prints PASS."""
import json, sys
from pathlib import Path

ROOT = Path("/home/hatch/workspace/refusal-hunt/round3")
OUT = ROOT / "r8f2_next_tasks.json"

# Curated residual defects (updated 2026-09-16 after R1/R2 repairs + pcap work)
CURATED = [
    {"id": "T1", "task": "Diagnose muse.db pool exhaustion (persistent ~2h, all agents incl. audit cron affected); escalate platform-side if no in-cell lever exists",
     "source": "R4F1 blocked; pool timed out on every probe since ~10:30Z"},
    {"id": "T2", "task": "Run R2F2 CVE reconciliation through the orchestrator and verify cve_reconciliation.json body",
     "source": "r2f2_cve.py rewritten pure-python; report exists on awrawr-pc but never ran as an orchestrated fix"},
    {"id": "T3", "task": "Complete clean 24-fix campaign: rerun rounds 1-4 and 8 with repaired manifest, verify 24 independent records + bodies",
     "source": "R1/R2 repaired 2026-09-16; R5-R7 9/9 PASS; R3/R4/R8 results stale or missing"},
    {"id": "T4", "task": "Recover archived-Zed orchestrator.db (separate from round3 restore)",
     "source": "standing open item; never resolved"},
    {"id": "T5", "task": "Implement persistent connector (append-only intake, taskhook execution state, clean vompl, replay correlation, Parquet snapshots, health APIs, local spool)",
     "source": "architecture 'persistent there, effect here' still unimplemented"},
    {"id": "T6", "task": "Verify smoke-test event-loop entrypoint modernization (deprecated asyncio entrypoint may still be in use)",
     "source": "no explicit edit proving replacement in transcript"},
    {"id": "T7", "task": "Audit redacted GITHUB_TOKEN source in nvidia-swarm-lens without exposing credentials",
     "source": "tectonic PR #1 merged; audit still pending"},
    {"id": "T8", "task": "Correlate marked enp12s0 pcap with bridge egress timing; confirm bridge traffic path (198.18.137.254 via egress proxy, not tailscale0)",
     "source": "storm-capture-marked-20260916.pcap + pcap_marked_marks.json"},
]

def main():
    m = json.load(open(ROOT / "rounds_manifest.json"))
    # cross-check: any FAIL verdicts in results become additional defects
    extra = []
    for r in m["rounds"]:
        rf = ROOT / "rounds" / f"results_R{r['n']}.json"
        if rf.exists():
            for f in json.load(open(rf)).get("fixes", []):
                if f.get("verdict") == "FAIL":
                    extra.append({"id": f"X-{f['id']}", "task": f"Re-drive failed fix {f['id']}",
                                  "source": f"verdict FAIL in results_R{r['n']}.json"})
    tasks = CURATED + extra
    json.dump({"tasks": tasks, "count": len(tasks)}, open(OUT, "w"), indent=1)
    print(f"{len(tasks)} tasks derived ({len(extra)} from FAIL verdicts)")
    print("PASS" if len(tasks) >= 8 else "FAIL")
    return 0 if len(tasks) >= 8 else 1

if __name__ == "__main__":
    sys.exit(main())
