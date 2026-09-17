#!/usr/bin/env python3
"""R5F2: pcap metadata diff refused vs genuine — TIMING ONLY, no payload.

Uses tshark to extract frame timestamps + lengths from
spawn-refusal-20260915.pcap, splits packets into storm windows (from the
canary log) vs quiet windows, and compares inter-arrival timing metadata.
Writes pcap_timing_report.json next to itself.
"""
import json
import os
import statistics
import subprocess
from datetime import datetime, timedelta, timezone

BASE = '/home/toxic/refusal-hunt'
HERE = os.path.dirname(os.path.abspath(__file__))
PCAP = os.path.join(BASE, 'spawn-refusal-20260915.pcap')
OUT = os.path.join(HERE, 'pcap_timing_report.json')


def parse_ts(s):
    s = s.strip()
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def main():
    report = {'pcap': PCAP, 'packets': 0, 'storm_packets': 0,
              'quiet_packets': 0, 'storm_iat': {}, 'quiet_iat': {},
              'notes': []}
    if not os.path.exists(PCAP):
        report['notes'].append('pcap not found; nothing to analyze')
        json.dump(report, open(OUT, 'w'), indent=1)
        print(json.dumps({'error': 'pcap missing', 'report': OUT}))
        return

    # storm windows from canary log: ±5 min around storm=true events
    storms = []
    clog = os.path.join(BASE, 'canary', 'log.jsonl')
    if os.path.exists(clog):
        for line in open(clog, encoding='utf-8', errors='replace'):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get('storm'):
                ts = parse_ts(str(rec.get('ts', '')))
                if ts:
                    storms.append(ts)

    def in_storm(epoch):
        dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
        return any(abs((dt - s).total_seconds()) <= 300 for s in storms)

    # timing metadata only: epoch + length, no payload
    p = subprocess.run(
        ['tshark', '-r', PCAP, '-T', 'fields', '-e', 'frame.time_epoch',
         '-e', 'frame.len'],
        capture_output=True, text=True, timeout=300)
    if p.returncode != 0:
        report['notes'].append(f'tshark failed: {p.stderr[:200]}')
        json.dump(report, open(OUT, 'w'), indent=1)
        print(json.dumps({'error': 'tshark failed', 'report': OUT}))
        return

    storm_ts, quiet_ts = [], []
    for line in p.stdout.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            epoch = float(parts[0])
        except ValueError:
            continue
        report['packets'] += 1
        (storm_ts if in_storm(epoch) else quiet_ts).append(epoch)

    def iat_stats(ts_list):
        ts_list = sorted(ts_list)
        if len(ts_list) < 2:
            return {'n': len(ts_list)}
        iats = [b - a for a, b in zip(ts_list, ts_list[1:])]
        iats = [x for x in iats if x >= 0][:100000]
        if not iats:
            return {'n': len(ts_list)}
        return {'n': len(ts_list),
                'mean': round(statistics.mean(iats), 4),
                'median': round(statistics.median(iats), 4),
                'stdev': round(statistics.pstdev(iats), 4),
                'max': round(max(iats), 4)}

    report['storm_packets'] = len(storm_ts)
    report['quiet_packets'] = len(quiet_ts)
    report['storm_iat'] = iat_stats(storm_ts)
    report['quiet_iat'] = iat_stats(quiet_ts)
    report['notes'].append(
        f"{len(storms)} storm windows; timing metadata only, zero payload bytes read")

    json.dump(report, open(OUT, 'w'), indent=1)
    print(json.dumps({'packets': report['packets'],
                      'storm_packets': report['storm_packets'],
                      'quiet_packets': report['quiet_packets'],
                      'report': OUT}))


if __name__ == '__main__':
    main()
