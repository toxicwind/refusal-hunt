#!/usr/bin/env python3
"""R8F1: rounds 1-7 effectiveness report. Reads all round result files and the
manifest, writes r8f1_report.json, prints PASS/FAIL."""
import json, sys
from pathlib import Path

ROOT = Path("/home/hatch/workspace/refusal-hunt/round3")
OUT = ROOT / "r8f1_report.json"

def main():
    m = json.load(open(ROOT / "rounds_manifest.json"))
    report = {"rounds": {}, "totals": {"pass": 0, "fail": 0, "other": 0}, "missing": []}
    for r in m["rounds"][:7]:
        n = r["n"]
        rf = ROOT / "rounds" / f"results_R{n}.json"
        if not rf.exists():
            report["missing"].append(n)
            continue
        d = json.load(open(rf))
        fixes = d.get("fixes", [])
        counts = {}
        for f in fixes:
            v = f.get("verdict", "UNKNOWN")
            counts[v] = counts.get(v, 0) + 1
            if v == "PASS": report["totals"]["pass"] += 1
            elif v == "FAIL": report["totals"]["fail"] += 1
            else: report["totals"]["other"] += 1
        report["rounds"][n] = {"fix_count": len(fixes), "verdicts": counts}
    json.dump(report, open(OUT, "w"), indent=1)
    print(json.dumps(report["totals"]))
    if report["missing"] or report["totals"]["fail"]:
        print("FAIL")
        return 1
    print("PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
