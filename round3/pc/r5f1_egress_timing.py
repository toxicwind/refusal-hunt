#!/usr/bin/env python3
"""R5F1: egress timing correlator — canary storm timestamps vs proxy/egress logs.

Timing metadata only. Writes egress_timing_report.json next to itself.
Honest about what it finds: if no proxy logs exist, it says so.
"""
import glob
import json
import os
import re
from datetime import datetime, timedelta, timezone

BASE = '/home/toxic/refusal-hunt'
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'egress_timing_report.json')

TS_RE = re.compile(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})')


def parse_ts(s):
    s = s.strip().replace(' ', 'T')
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def main():
    report = {'canary_events': 0, 'storm_windows': [], 'proxy_candidates': {},
              'correlations': [], 'notes': []}

    # 1. canary storm events
    clog = os.path.join(BASE, 'canary', 'log.jsonl')
    storms = []
    if os.path.exists(clog):
        for line in open(clog, encoding='utf-8', errors='replace'):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            report['canary_events'] += 1
            if rec.get('storm'):
                ts = parse_ts(str(rec.get('ts', '')))
                if ts:
                    storms.append(ts)
    report['storm_windows'] = [t.isoformat() for t in storms]
    report['notes'].append(f'{len(storms)} storm=true canary events')

    # 2. proxy/egress log candidates on this box
    candidates = {
        'mcpproxy': '/var/log/mcpproxy',
        'gssproxy': '/var/log/gssproxy',
        'squid': '/var/log/squid/access.log',
        'tinyproxy': '/var/log/tinyproxy/tinyproxy.log',
    }
    for name, path in candidates.items():
        if os.path.isdir(path):
            files = sorted(glob.glob(os.path.join(path, '*')))[:5]
        elif os.path.isfile(path):
            files = [path]
        else:
            files = []
        report['proxy_candidates'][name] = {'path': path, 'files': files}

    # 3. correlate: for each storm event, count timestamped lines in ±5 min
    for t in storms[-10:]:  # bound the work: last 10 storm events
        lo, hi = t - timedelta(minutes=5), t + timedelta(minutes=5)
        corr = {'storm_ts': t.isoformat(), 'window_hits': {}}
        for name, info in report['proxy_candidates'].items():
            hits = 0
            for fp in info['files']:
                try:
                    with open(fp, encoding='utf-8', errors='replace') as fh:
                        for line in fh:
                            m = TS_RE.search(line)
                            if not m:
                                continue
                            lts = parse_ts(m.group(1))
                            if lts and lo <= lts <= hi:
                                hits += 1
                                if hits > 5000:
                                    break
                except (OSError, PermissionError):
                    pass
            corr['window_hits'][name] = hits
        report['correlations'].append(corr)

    if not any(report['proxy_candidates'][n]['files']
               for n in report['proxy_candidates']):
        report['notes'].append('no proxy/egress log files found on this box; '
                               'correlation limited to canary timing itself')

    json.dump(report, open(OUT, 'w'), indent=1)
    print(json.dumps({'storms': len(storms),
                      'proxy_logs_found': sum(
                          1 for n in report['proxy_candidates']
                          if report['proxy_candidates'][n]['files']),
                      'report': OUT}))


if __name__ == '__main__':
    main()
