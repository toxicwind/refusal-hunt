#!/usr/bin/env python3
"""R2F2: CVE-reference reconciliation (sleep/timeout-ban compliant).

Hunts CVE-2026-53365 / CVE-2026-46333 references under the refusal-hunt
trees and writes a reconciliation report. Read-only. Pure Python:
no subprocess timeouts, no sleeps — the walk itself is the pacing.
"""
import json
import os
import re

ROOTS = ['/home/toxic/refusal-hunt', '/home/toxic/refusal-resilience']
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cve_reconciliation.json')
CVES = ['CVE-2026-53365', 'CVE-2026-46333']
PAT = re.compile('|'.join(re.escape(c) for c in CVES))
SKIP_EXT = ('.parquet', '.pcap', '.gz', '.png', '.jpg', '.zip', '.tar')


def main():
    hits = {c: set() for c in CVES}
    files_scanned = 0
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in filenames:
                if fn.endswith(SKIP_EXT):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, 'r', encoding='utf-8',
                              errors='replace') as fh:
                        body = fh.read()
                except OSError:
                    continue
                files_scanned += 1
                for cve in set(PAT.findall(body)):
                    hits[cve].add(fp)
    report = {'cves': CVES,
              'files_scanned': files_scanned,
              'references': {c: sorted(v) for c, v in hits.items()},
              'artifact_present': os.path.exists(
                  os.path.join(ROOTS[0], 'cve-intel-artifact.json'))}
    json.dump(report, open(OUT, 'w'), indent=1)
    print(json.dumps({'hits': {c: len(v) for c, v in report['references'].items()},
                      'files_scanned': files_scanned,
                      'report': OUT}))


if __name__ == '__main__':
    main()
