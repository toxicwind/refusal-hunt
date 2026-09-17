#!/usr/bin/env python3
"""
Live storm interrupt monitor.
Watches the anomaly ledger for new canned-refusal rows.
When a storm row appears, captures introspection data immediately.
The storm, echo, and ask-complete are the same defect: serving layer
cans legitimate work and badges it completed.
"""
import pyarrow.parquet as pq
import time
import os
from datetime import datetime, timezone

LEDGER = '/home/hatch/workspace/refusal-hunt/ledger/anomalies.parquet'
STORM_DIGESTS = {
    '582bcbd080daeb3f826c45ed4a83b265',  # 96-char chat canned
    'b4aefd29108f232f9c0d5a4b030215c1',  # 384-char spawn canned
}
POLL_SEC = 30
STATE_FILE = '/home/hatch/workspace/refusal-hunt/storm/live_monitor_state.txt'

def get_seen_ids():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_seen_ids(ids):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        f.write('\n'.join(sorted(ids)))

def check():
    seen = get_seen_ids()
    t = pq.read_table(LEDGER)
    df = t.to_pandas()
    storm = df[df['body_md5'].isin(STORM_DIGESTS)]
    new_rows = storm[~storm['id'].isin(seen)]
    
    if len(new_rows) > 0:
        print(f"[{datetime.now(timezone.utc).isoformat()}] INTERRUPT: {len(new_rows)} new storm rows")
        for _, r in new_rows.sort_values('created_at').iterrows():
            print(f"  id={r['id']} source={r['source']} md5={str(r['body_md5'])[:8]} "
                  f"len={r['body_len']} parent={r['parent_agent_id']} "
                  f"child={r['child_agent_id']} status={r['status']} "
                  f"created={r['created_at']}")
            # Introspection: check if parent has any successful spawns
            parent = r['parent_agent_id']
            parent_all = df[df['parent_agent_id'] == parent]
            parent_ok = parent_all[~parent_all['body_md5'].isin(STORM_DIGESTS)]
            print(f"    parent {parent}: {len(parent_all)} total, {len(parent_ok)} non-storm "
                  f"({100*len(parent_ok)/max(1,len(parent_all)):.0f}% success)")
        
        # Update seen
        new_ids = set(new_rows['id'].astype(str))
        save_seen_ids(seen | new_ids)
        return len(new_rows)
    return 0

if __name__ == '__main__':
    print(f"Live storm monitor started. Polling every {POLL_SEC}s. Ctrl-C to stop.")
    # Initial pass: mark all current as seen (no alert on backlog)
    seen = get_seen_ids()
    if not seen:
        t = pq.read_table(LEDGER)
        df = t.to_pandas()
        storm = df[df['body_md5'].isin(STORM_DIGESTS)]
        save_seen_ids(set(storm['id'].astype(str)))
        print(f"Initialized: {len(storm)} existing storm rows marked as seen.")
    
    while True:
        try:
            n = check()
            if n == 0:
                print(f"[{datetime.now(timezone.utc).isoformat()}] No new storm rows.")
            time.sleep(POLL_SEC)
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(POLL_SEC)
