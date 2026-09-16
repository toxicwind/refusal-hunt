#!/usr/bin/env python3
"""R2F2: CVE-reference reconciliation.

Hunts CVE-2026-53365 / CVE-2026-46333 references under the refusal-hunt
trees and writes a reconciliation report. Read-only.
"""
import json
import os
import re
import subprocess

ROOTS = ['/home/toxic/refusal-hunt', '/home/toxic/refusal-resilience']
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cve_reconciliation.json')
CVES = ['CVE-2026-53365', 'CVE-2026-46333']


def main():
    hits = {c: [] for c in CVES}
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        p = subprocess.run(
            ['rg', '-l', '|'.join(CVES), root, '-g', '!*.parquet', '-g', '!*.pcap'],
            capture_output=True, text=True, timeout=120)
        for fp in p.stdout.splitlines():
            try:
                q = subprocess.run(['rg', '-o', '|'.join(CVES), fp],
                                   capture_output=True, text=True, timeout=30)
                for cve in set(q.stdout.split()):
                    if cve in hits:
                        hits[cve].append(fp)
            except Exception:
                pass
    report = {'cves': CVES,
              'references': {c: sorted(set(v)) for c, v in hits.items()},
              'artifact_present': os.path.exists(
                  os.path.join(ROOTS[0], 'cve-intel-artifact.json'))}
    json.dump(report, open(OUT, 'w'), indent=1)
    print(json.dumps({'hits': {c: len(v) for c, v in report['references'].items()},
                      'report': OUT}))


if __name__ == '__main__':
    main()
