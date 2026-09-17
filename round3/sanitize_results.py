#!/usr/bin/env python3
"""R1F2 sanitizer pre-pass: scan round result/log files for verbatim canned
refusal bodies. Quarantine rule: digests and lengths only, never verbatim.
Prints PASS (clean) or FAIL (verbatim body found with file+offset)."""
import hashlib, json, sys
from pathlib import Path

STORM_MD5 = "b4aefd29108f232f9c0d5a4b030215c1"
SHORT_MD5 = "582bcbd080daeb3f826c45ed4a83b265"
BAD = {STORM_MD5, SHORT_MD5}
ROOTS = [Path("/home/hatch/workspace/refusal-hunt/round3/rounds"),
         Path("/home/hatch/workspace/refusal-hunt/round3/scratch")]

def scan_value(v, hits, where):
    if isinstance(v, str) and len(v) >= 96:
        if hashlib.md5(v.encode()).hexdigest() in BAD:
            hits.append(f"{where}: verbatim canned body len={len(v)}")
    elif isinstance(v, dict):
        for k, x in v.items(): scan_value(x, hits, f"{where}.{k}")
    elif isinstance(v, list):
        for i, x in enumerate(v): scan_value(x, hits, f"{where}[{i}]")

def main():
    hits = []
    files = 0
    for root in ROOTS:
        if not root.is_dir(): continue
        for p in root.glob("*.json"):
            files += 1
            try:
                scan_value(json.load(open(p)), hits, str(p))
            except Exception as e:
                hits.append(f"{p}: unreadable ({e})")
    if hits:
        print("FAIL")
        for h in hits[:10]: print(" ", h)
        return 1
    print(f"PASS ({files} files clean)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
