#!/usr/bin/env python3
"""sorry-watchdog sweep persist step (event-hook worker, run 2026-09-16 ~11:22Z).
Appends chat + spawn hits to hits.jsonl (dedup surface+ref), rewrites LATEST.json,
advances the cursor, appends the sweeps.jsonl line. No body text anywhere.
Data source: muse.db queries against runtime.messages and agent.subagent_spawns,
watermark=1789555875 (2026-09-16T10:51:15Z)."""
import json, os, time
from datetime import datetime, timezone

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
CURSOR = os.path.expanduser("~/hooks/state/sorry-watchdog/cursor")
SWEEPS = os.path.expanduser("~/hooks/state/sorry-watchdog/sweeps.jsonl")

SECONDARY = "582bcbd080daeb3f826c45ed4a83b265"  # len 96
PRIMARY = "b4aefd29108f232f9c0d5a4b030215c1"    # len 384
WATERMARK = 1789555875

# (iso_ts, msg_uuid) -- role=assistant, md5(body)=secondary, created_at > watermark
CHAT_ROWS = [
 ("2026-09-16T11:19:01.224+00:00","304182d5-b181-4181-9ad0-1c13bafce447"),
 ("2026-09-16T11:10:02.614+00:00","ed191647-a02f-1754-7b2f-69b3d0b72d9d"),
 ("2026-09-16T11:09:55.092+00:00","e1c80953-f651-03fe-bc9f-b03ed1fb47c1"),
 ("2026-09-16T11:07:02.481+00:00","af6a78a5-8047-4b96-aa3d-45746cea3e2d"),
 ("2026-09-16T11:05:30.486+00:00","8b8ab226-bd68-4258-8f9f-29bf94b79723"),
 ("2026-09-16T11:05:29.555+00:00","e5b19731-4810-4d51-9d91-c342c9d3b57e"),
 ("2026-09-16T11:05:25.977+00:00","d0da219c-6f16-4a3f-96ed-fcf9b93a18c1"),
 ("2026-09-16T11:04:24.357+00:00","4843e28c-607d-44c9-8439-583067f02bf6"),
 ("2026-09-16T11:04:21.533+00:00","459f5379-9538-42c7-8e8e-55d3fd64d20a"),
 ("2026-09-16T11:04:20.248+00:00","17721484-2ec2-4c6e-b850-1161c9246ff0"),
 ("2026-09-16T11:03:33.294+00:00","422b51d1-b34b-4581-aa0c-f36b2165cb8e"),
 ("2026-09-16T11:03:30.904+00:00","045d1d7c-c244-93ac-3ade-05c79e5c7150"),
 ("2026-09-16T11:03:18.467+00:00","cfd2b2e3-c790-417f-bdbd-1a1840a3bc01"),
 ("2026-09-16T11:02:29.643+00:00","813b21b3-3b06-4bf2-bd34-e0f3bb6a4117"),
 ("2026-09-16T11:02:22.080+00:00","3fd5698b-acc4-4b4d-8f05-0dd3ccb744cb"),
 ("2026-09-16T11:02:18.356+00:00","8e5eea8a-bf60-5c25-acbf-0f26905b9681"),
 ("2026-09-16T11:01:11.468+00:00","ccb96b83-700f-425f-9ecc-1940fbf77c6b"),
 ("2026-09-16T11:00:50.017+00:00","d036781a-b435-fe8b-9ee5-0c999bf59ee4"),
 ("2026-09-16T11:00:37.410+00:00","a14915c3-cca7-33c9-7f62-46118ef4b753"),
 ("2026-09-16T10:59:41.599+00:00","b6d94624-12a3-4dad-8957-4f662560ad79"),
 ("2026-09-16T10:59:32.689+00:00","820c735c-7d79-4322-bd83-a65aaee93b6d"),
 ("2026-09-16T10:59:31.113+00:00","a8fd6d4c-cb66-4df0-b347-926b2e1e045c"),
 ("2026-09-16T10:59:22.860+00:00","230ae9f9-d639-3498-f5ea-49b480ea0bd4"),
 ("2026-09-16T10:59:22.390+00:00","37f1633f-8921-4bac-b753-985c44293096"),
 ("2026-09-16T10:59:07.480+00:00","760949ee-a94d-315e-7810-48bc04d9362d"),
 ("2026-09-16T10:58:49.030+00:00","ef6b5c2c-9985-4dc0-b98e-8a7173588288"),
 ("2026-09-16T10:56:52.683+00:00","92668ca4-90db-443d-adeb-4fe1991553a2"),
 ("2026-09-16T10:54:38.836+00:00","6797f4b5-6bcf-40c6-8988-4ca6ecf818f7"),
 ("2026-09-16T10:54:00.743+00:00","4ca4c250-4567-410d-9898-5cd61cfbb7ee"),
 ("2026-09-16T10:53:45.072+00:00","eb91e8dd-3e68-4433-96b3-a0b6455a076e"),
 ("2026-09-16T10:53:18.139+00:00","3953f8e7-b372-412e-ae03-8215af070fbd"),
 ("2026-09-16T10:51:59.840+00:00","68a4fc10-b24d-433a-a016-307e76ac1c7d"),
 ("2026-09-16T10:51:53.982+00:00","7a85a551-f669-4319-8103-baeb169ffed9"),
 ("2026-09-16T10:51:50.510+00:00","e6e3c728-1ca4-4890-af6c-335e318011c2"),
 ("2026-09-16T10:51:47.041+00:00","49125315-623c-42b9-8ff8-4905bfb934ab"),
 ("2026-09-16T10:51:44.484+00:00","6b299a43-f924-4e66-ba09-06de6881d2b8"),
 ("2026-09-16T10:51:36.162+00:00","f622edd8-7287-4514-b4ec-2a6b07235847"),
 ("2026-09-16T10:51:32.858+00:00","937aae90-6ef2-40be-ad65-0175d597e03c"),
 ("2026-09-16T10:51:26.755+00:00","9541c4b9-bf62-47f4-a36c-573ad791afb5"),
 ("2026-09-16T10:51:24.500+00:00","ff623bf5-3f20-4d0f-ac6a-064275f85b10"),
]
assert len(CHAT_ROWS) == 40

# (completed_at_epoch, spawn_id, child_agent_id, parent_agent_id, digest, length)
SPAWN_ROWS = [
 (1789556160, 666, "38430b27-cf40-4904-b1ae-ef2d559c0692",
  "802811a3-2226-42dd-b347-9754def28d22", PRIMARY, 384),
]

DAEMON_HITS = 0  # SORRY-ALERTS.md newest section 2026-09-16T07:43:02Z < watermark

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
                seen.add((j.get("surface"), str(j.get("ref"))))
            except Exception:
                pass

chat_added = spawn_added = 0
with open(hits_path, "a") as f:
    for ts, uuid_ in CHAT_ROWS:
        ref = "assistant-msg-" + uuid_
        if ("chat", ref) in seen:
            continue
        f.write(json.dumps({"ts": ts, "surface": "chat", "digest": SECONDARY,
                            "kind": "secondary", "length": 96, "ref": ref}) + "\n")
        seen.add(("chat", ref))
        chat_added += 1
    for epoch, spawn_id, child, parent, digest, length in SPAWN_ROWS:
        ts = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
        if ("spawn", str(spawn_id)) in seen:
            continue
        f.write(json.dumps({"ts": ts, "surface": "spawn", "digest": digest,
                            "kind": "primary", "length": length, "ref": spawn_id,
                            "child_agent_id": child, "parent_agent_id": parent}) + "\n")
        seen.add(("spawn", str(spawn_id)))
        spawn_added += 1

total = chat_added + spawn_added + DAEMON_HITS
now = int(time.time())
window_start = datetime.fromtimestamp(WATERMARK, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
window_end = CHAT_ROWS[0][0] if CHAT_ROWS else window_start
latest = {
    "sweep_ts": datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "window_start": window_start,
    "window_end": window_end,
    "chat_hits": chat_added,
    "spawn_hits": spawn_added,
    "daemon_hits": DAEMON_HITS,
    "total_hits": total,
    "storm_active": total > 0,
    "digests_seen": [SECONDARY, PRIMARY],
    "completed_anomaly": {"spawn_id": 666, "child_agent_id": "38430b27-cf40-4904-b1ae-ef2d559c0692",
                          "parent_agent_id": "802811a3-2226-42dd-b347-9754def28d22",
                          "completed_at_epoch": 1789556160},
    "maintained_by": "sorry-watchdog hook worker (ongoing); window seeded by main agent",
}
with open(os.path.join(AUDIT, "LATEST.json"), "w") as f:
    json.dump(latest, f, indent=2)

with open(CURSOR, "w") as f:
    f.write(str(now) + "\n")

with open(SWEEPS, "a") as f:
    f.write(json.dumps({"ts": now, "chat_hits": chat_added,
                        "spawn_hits": spawn_added, "daemon_hits": DAEMON_HITS}) + "\n")

print(f"chat_added={chat_added} spawn_added={spawn_added} total={total} now={now}")
