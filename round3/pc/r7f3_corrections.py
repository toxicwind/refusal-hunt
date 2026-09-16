#!/usr/bin/env python3
"""R7F3: corrections parquet on awrawr-pc.

Reads canary snapshot CSVs, classifies each spawn row by body hash/length,
writes corrections.parquet (+ corrections_summary.json). Digests only —
no refusal body text is stored.
"""
import csv
import glob
import hashlib
import json
import os

BASE = '/home/toxic/refusal-hunt'
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PARQUET = os.path.join(HERE, 'corrections.parquet')
OUT_JSON = os.path.join(HERE, 'corrections_summary.json')

STORM_MD5 = 'b4aefd29108f232f9c0d5a4b030215c1'   # 384-char canned body
SHORT_MD5 = '582bcbd080daeb3f826c45ed4a83b265'   # 96-char canned variant


def classify(fr_md5, fr_len):
    if fr_md5 == STORM_MD5:
        return 'refused_as_completed'
    if fr_md5 == SHORT_MD5:
        return 'refused_short_variant'
    try:
        if int(fr_len) > 200:
            return 'genuine'
    except (TypeError, ValueError):
        pass
    return 'other'


def main():
    rows = []
    files = sorted(glob.glob(os.path.join(BASE, 'canary', 'snapshot-*.csv')))
    for fp in files:
        with open(fp, newline='', encoding='utf-8', errors='replace') as fh:
            for rec in csv.DictReader(fh):
                rows.append({
                    'snapshot': os.path.basename(fp),
                    'spawn_id': rec.get('spawn_id', ''),
                    'ledger_status': rec.get('status', ''),
                    'fr_md5': rec.get('fr_md5', ''),
                    'fr_len': rec.get('fr_len', ''),
                    'true_label': classify(rec.get('fr_md5', ''), rec.get('fr_len', '')),
                    'created_epoch': rec.get('created_epoch', ''),
                })

    summary = {'snapshots': len(files), 'rows': len(rows), 'by_label': {}}
    for r in rows:
        summary['by_label'][r['true_label']] = summary['by_label'].get(
            r['true_label'], 0) + 1

    wrote = None
    try:
        import pandas as pd
        df = pd.DataFrame(rows)
        df.to_parquet(OUT_PARQUET, compression='zstd', index=False)
        wrote = OUT_PARQUET
    except Exception as e:
        out_csv = os.path.join(HERE, 'corrections.csv')
        if rows:
            with open(out_csv, 'w', newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
        summary['parquet_fallback'] = f'csv ({e})'
        wrote = out_csv

    summary['output'] = wrote
    json.dump(summary, open(OUT_JSON, 'w'), indent=1)
    print(json.dumps({'rows': len(rows), 'by_label': summary['by_label'],
                      'output': wrote}))


if __name__ == '__main__':
    main()
