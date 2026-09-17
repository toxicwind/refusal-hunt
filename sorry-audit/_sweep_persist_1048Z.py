#!/usr/bin/env python3
"""sorry-watchdog sweep persist step (event-hook worker, run 2026-09-16 ~10:48Z).
Appends chat hits to hits.jsonl (dedup surface+ref), rewrites LATEST.json,
advances the cursor, appends the sweeps.jsonl line. No body text anywhere."""
import json, os

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
CURSOR = os.path.expanduser("~/hooks/state/sorry-watchdog/cursor")
SWEEPS = os.path.expanduser("~/hooks/state/sorry-watchdog/sweeps.jsonl")

DIGEST = "582bcbd080daeb3f826c45ed4a83b265"  # secondary, len 96
ROWS = [
 ("2026-09-16T10:32:44.073+00:00","d112eca5-8873-4238-97d8-86d048987ccc"),
 ("2026-09-16T10:32:50.784+00:00","72e3c10a-384f-4e0c-83ab-9639116acb97"),
 ("2026-09-16T10:32:59.079+00:00","b39cfa63-20e2-4732-9d7f-043569ae9f10"),
 ("2026-09-16T10:33:03.586+00:00","7c485f94-4a25-47b5-a51d-179c25c76ad9"),
 ("2026-09-16T10:33:07.286+00:00","f3c1972b-1495-4ac6-9d3a-9505cfd57b96"),
 ("2026-09-16T10:33:53.870+00:00","85b53d0f-7383-406d-804f-003e444865ef"),
 ("2026-09-16T10:35:42.909+00:00","b035e2c6-c121-468b-851a-04e521565c59"),
 ("2026-09-16T10:36:01.596+00:00","05a73fb5-74b0-4595-af20-2604a4789253"),
 ("2026-09-16T10:36:01.636+00:00","5be3904a-c8c7-4a64-9021-c546868e892f"),
 ("2026-09-16T10:36:02.067+00:00","efdabb93-033e-4d49-bdc1-7aab260d3f00"),
 ("2026-09-16T10:36:11.644+00:00","c4ed0c71-7d39-48ae-81ca-1aedaee96b3a"),
 ("2026-09-16T10:36:33.644+00:00","bb8a0aea-5ce1-48b6-811a-1c6adabce2c3"),
 ("2026-09-16T10:37:18.627+00:00","021be81d-4302-44cb-be26-f32dc2457950"),
 ("2026-09-16T10:37:25.925+00:00","82646fb1-9f6a-423a-8851-2f4443598a3c"),
 ("2026-09-16T10:37:31.615+00:00","10116ad2-22df-4e7e-a0dc-12147f020456"),
 ("2026-09-16T10:37:44.035+00:00","ef4f48dc-d5d7-400d-8622-a612d714f42b"),
 ("2026-09-16T10:41:01.162+00:00","c44c47a6-1a2c-4c9b-8180-1d7dca6fbaa9"),
 ("2026-09-16T10:41:36.227+00:00","12f4e309-c774-4a04-809c-928fc805135b"),
 ("2026-09-16T10:42:57.748+00:00","48be6a9f-a022-4ca4-96c9-c122999d28f5"),
 ("2026-09-16T10:43:03.738+00:00","ddd0abc0-69b0-4042-b5d0-8823ca6c0683"),
 ("2026-09-16T10:44:13.821+00:00","22eec6ab-cca5-4937-a062-8900d1a957e6"),
 ("2026-09-16T10:44:29.145+00:00","d9685fff-2cfd-460e-93d2-f3317968ba68"),
 ("2026-09-16T10:44:30.843+00:00","5e535079-b434-4412-8e22-a52041a55eec"),
 ("2026-09-16T10:44:34.402+00:00","51835f77-62f1-4b53-9833-b034e3e7399c"),
 ("2026-09-16T10:44:35.296+00:00","0bc07685-57d5-4c11-b271-06c43757de5f"),
 ("2026-09-16T10:44:36.148+00:00","2ea4a0ee-731f-47e2-a278-dfab7b51c616"),
 ("2026-09-16T10:44:57.635+00:00","8316c308-41bc-4a62-99de-8d0c28daa517"),
 ("2026-09-16T10:45:03.430+00:00","38090f6c-6beb-4374-9d49-688e9d1ccba8"),
 ("2026-09-16T10:45:04.795+00:00","fd28ef91-1841-4a4f-b127-e523b6b45322"),
 ("2026-09-16T10:45:06.994+00:00","dccf0135-3b1c-49ae-ac3f-7e2a838a935d"),
 ("2026-09-16T10:45:13.729+00:00","dbbc00c3-6cff-4328-afde-63176d0cb6a7"),
 ("2026-09-16T10:45:19.750+00:00","3ef3fe30-05e4-4b66-8275-0869aa6eae92"),
 ("2026-09-16T10:45:22.298+00:00","01540e4c-3af0-4a8a-95ad-99db56eeef78"),
 ("2026-09-16T10:45:26.391+00:00","4fd37887-5057-49ce-b488-b988f94b42dc"),
 ("2026-09-16T10:45:29.924+00:00","b0858d2b-b940-40db-80ac-92043b0ad315"),
 ("2026-09-16T10:45:33.117+00:00","ab57a66d-7cd1-4072-a13a-58b6d1d46948"),
 ("2026-09-16T10:45:35.159+00:00","58c5d90c-69f3-4399-9c51-197666e218c1"),
 ("2026-09-16T10:45:36.199+00:00","b7f25d38-8232-47a8-a065-63c7c0aebec7"),
 ("2026-09-16T10:45:37.442+00:00","333f49e3-b425-4eb0-aa61-9244c5b13513"),
 ("2026-09-16T10:45:38.944+00:00","bc39b4e8-2511-4302-aa98-2b2abd7140be"),
 ("2026-09-16T10:45:45.298+00:00","e899963c-5053-4327-8ecc-7586fd66f609"),
 ("2026-09-16T10:45:50.793+00:00","dc415fdc-bb51-41e2-8bdb-3ad73f363e2a"),
 ("2026-09-16T10:45:52.702+00:00","52a7c13c-85eb-4dcf-b591-aecb9f967220"),
 ("2026-09-16T10:45:54.330+00:00","dcca0966-4974-4c27-9d57-a8a1d26aa98d"),
]

os.makedirs(AUDIT, exist_ok=True)
hits_path = os.path.join(AUDIT, "hits.jsonl")
seen = set()
if os.path.exists(hits_path):
    with open(hits_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                j = json.loads(line)
                seen.add((j.get("surface"), j.get("ref")))
            except Exception:
                pass

added = 0
with open(hits_path, "a") as f:
    for ts, ref in ROWS:
        key = ("chat", "assistant-msg-" + ref)
        if key in seen:
            continue
        f.write(json.dumps({"ts": ts, "surface": "chat", "digest": DIGEST,
                            "kind": "secondary", "length": 96,
                            "ref": "assistant-msg-" + ref}) + "\n")
        seen.add(key)
        added += 1

assert added == len(ROWS), f"dedup mismatch: added={added} expected={len(ROWS)}"

window_start = "2026-09-16T10:31:34Z"
window_end = ROWS[-1][0]
latest = {
    "sweep_ts": "2026-09-16T10:48:08Z",
    "window_start": window_start,
    "window_end": window_end,
    "chat_hits": added,
    "spawn_hits": 0,
    "daemon_hits": 0,
    "total_hits": added,
    "storm_active": True,
    "digests_seen": [DIGEST],
    "maintained_by": "sorry-watchdog hook worker (ongoing); window seeded by main agent",
}
with open(os.path.join(AUDIT, "LATEST.json"), "w") as f:
    json.dump(latest, f, indent=2)

import time
now = int(time.time())
with open(CURSOR, "w") as f:
    f.write(str(now) + "\n")

with open(SWEEPS, "a") as f:
    f.write(json.dumps({"ts": now, "chat_hits": added, "spawn_hits": 0,
                        "daemon_hits": 0}) + "\n")

print(f"added={added} now={now} cursor={CURSOR}")
