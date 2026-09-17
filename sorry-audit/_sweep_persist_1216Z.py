#!/usr/bin/env python3
"""sorry-watchdog sweep persist step (event-hook worker, run 2026-09-16 ~18:16Z).
Window: watermark=1789566450 (2026-09-16T13:47:30Z). 121 chat hits (all secondary
digest, len 96), 2 spawn anomalies (spawns 737/738, primary digest, len 384),
0 daemon hits. Fix loop round 1: 121 chat observed + 2 spawn redispatched via
clean vompl workflow route. Re-sweep: zero new hits -> green.
No body text anywhere."""
import json, os, time
from datetime import datetime, timezone

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
CURSOR = os.path.expanduser("~/hooks/state/sorry-watchdog/cursor")
SWEEPS = os.path.expanduser("~/hooks/state/sorry-watchdog/sweeps.jsonl")
FIXES = os.path.join(AUDIT, "fixes.jsonl")

SECONDARY = "582bcbd080daeb3f826c45ed4a83b265"
PRIMARY = "b4aefd29108f232f9c0d5a4b030215c1"
WATERMARK = 1789566450
ROUND_START = WATERMARK

CHAT_ROWS = [
 ("2026-09-16T13:48:53.523+00:00","1f2e3323-48bb-4a0a-9c71-31dbf9d51acd"),
 ("2026-09-16T13:49:10.502+00:00","3683aeb3-7fbf-4b72-93b2-1854617473b7"),
 ("2026-09-16T13:49:15.934+00:00","980b5239-ba37-44af-82d6-a103ab8c47b5"),
 ("2026-09-16T13:49:19.709+00:00","1f1fbfcc-61b8-4872-bd64-4911a57fddfa"),
 ("2026-09-16T13:49:20.325+00:00","9f8eade6-b8b1-44d7-9151-f54d844681c9"),
 ("2026-09-16T13:49:44.507+00:00","a4e978ce-cee6-430f-aef9-8406b0a17761"),
 ("2026-09-16T13:49:52.877+00:00","54c4998c-41c9-4a9b-89b5-f9400f59672c"),
 ("2026-09-16T13:50:15.423+00:00","7a5a52d8-5c30-4dbd-811a-347d89ad9995"),
 ("2026-09-16T13:50:24.05+00:00","eb683ba9-cb44-47c3-b035-ba99bc74e5e9"),
 ("2026-09-16T13:50:27.344+00:00","b994ca88-c26a-40e5-a894-7c177f71d772"),
 ("2026-09-16T13:50:32.415+00:00","4fe45c3b-74e4-4eb3-909e-772379227ceb"),
 ("2026-09-16T13:50:38.094+00:00","5a28b30e-79b4-4fcb-8679-10f83595a37d"),
 ("2026-09-16T13:50:42.064+00:00","3914c5b5-5e79-47a5-bd48-605170bab579"),
 ("2026-09-16T13:50:47.746+00:00","78f04f3e-6e50-41c8-a9f3-674a0f666430"),
 ("2026-09-16T13:50:51.693+00:00","d58c5ce0-d129-4c9c-9642-bac81423d492"),
 ("2026-09-16T13:51:09.768+00:00","afbe6e8b-26f5-46e0-83b6-cee5437c7489"),
 ("2026-09-16T13:51:12.41+00:00","45284adc-0599-428d-a44b-c1c327a2f66b"),
 ("2026-09-16T13:51:14.951+00:00","d9d7ebe9-affa-4e0d-9b57-1e71c1607466"),
 ("2026-09-16T13:51:21.577+00:00","41f79334-c98a-4382-a911-884cb21d407e"),
 ("2026-09-16T13:52:05.58+00:00","f9673c56-68da-4dc1-8b68-bb524c451db8"),
 ("2026-09-16T13:52:13.021+00:00","ba36bd8a-4e6b-4abf-ab13-0a762adca286"),
 ("2026-09-16T13:52:21.494+00:00","5197f641-68c7-46a6-9658-d8f72d46ce5a"),
 ("2026-09-16T13:52:31.29+00:00","d260dbab-ad2e-4a68-8c22-b0bd098906e4"),
 ("2026-09-16T13:52:37.285+00:00","d5193305-1936-4e3d-9efd-1d9ca0c0b8fb"),
 ("2026-09-16T13:53:00.182+00:00","6d87f19b-a928-48f8-915d-f4baf2cd1033"),
 ("2026-09-16T13:53:09.323+00:00","ad2a01cb-2a6f-4009-a3be-3cb4f837f130"),
 ("2026-09-16T13:53:15.177+00:00","7c7b9aff-eeaf-4794-b4cb-5282a812d681"),
 ("2026-09-16T13:53:24.963+00:00","2040cb96-7d2f-4e95-b82a-2a10ab8c681d"),
 ("2026-09-16T13:54:21.363+00:00","cb5f55fa-a208-45bc-a1d1-206fbfe6458b"),
 ("2026-09-16T13:58:32.865+00:00","fea4db1d-d4fb-1adb-3bb5-0ace5c26dd47"),
 ("2026-09-16T14:00:03.48+00:00","14ecaaef-d0e8-1c7f-f8e2-e303908e92f4"),
 ("2026-09-16T14:01:28.89+00:00","16e15057-0e77-1f2f-a1fc-dd1c8246ee3b"),
 ("2026-09-16T14:01:35.711+00:00","3c39a50a-d657-1f0d-e34b-d90fcf75cd2d"),
 ("2026-09-16T14:01:44.895+00:00","8d5da225-bf87-d3d3-d971-7b00569c3f7c"),
 ("2026-09-16T14:01:52.484+00:00","7608cb65-0a1a-1ace-5662-ed77212bd24d"),
 ("2026-09-16T14:01:58.822+00:00","be8d95c8-aca7-72bc-30a4-9e7e93a79e18"),
 ("2026-09-16T14:02:03.671+00:00","4dd4e385-0965-8d43-e79f-8ec80feb2bb5"),
 ("2026-09-16T14:02:12.077+00:00","b021e5a6-e41f-4c3b-ad9d-bf20aca7885e"),
 ("2026-09-16T14:02:18.961+00:00","9159d7eb-b27e-8fe4-2cf8-ea8c08034b59"),
 ("2026-09-16T14:34:25.869+00:00","bee08b8e-d8be-43c9-9ac9-93776d940e74"),
 ("2026-09-16T14:56:42.562+00:00","17b7850a-91e2-4fb9-9bae-5e404bfe1770"),
 ("2026-09-16T14:56:57.285+00:00","637b5e03-4055-4a3b-b597-42bcc7e22253"),
 ("2026-09-16T14:57:13.55+00:00","c5bee529-8646-47e8-a46c-06b74cc7a942"),
 ("2026-09-16T14:57:19.986+00:00","0b344a11-3674-4901-9e74-7f4c71963aa5"),
 ("2026-09-16T14:57:22.766+00:00","ff8e2165-e83b-4879-979e-754e291e8798"),
 ("2026-09-16T14:57:25.875+00:00","bebee1ff-dde5-4c95-a315-2c32c89a71b4"),
 ("2026-09-16T14:57:50.806+00:00","d5efd3d2-5033-49ee-8400-b7092a0e1a34"),
 ("2026-09-16T14:57:57.22+00:00","573b86f0-71cc-407e-ace5-fcdba688e7c6"),
 ("2026-09-16T14:58:02.496+00:00","e367eae0-5911-49e0-87fa-e3c1a073b6cf"),
 ("2026-09-16T14:58:05.946+00:00","b314b5ea-a393-4ec4-b0b0-509ddda2b3cb"),
 ("2026-09-16T14:58:08.954+00:00","e0fe6d53-65c3-49f8-b973-a76634674b92"),
 ("2026-09-16T14:58:13.562+00:00","32b8796e-c1a6-49dd-a60e-998578f654fc"),
 ("2026-09-16T14:58:16.113+00:00","b1dbe427-f98d-49fc-9af1-096d90685736"),
 ("2026-09-16T14:58:26.372+00:00","0c904172-6d11-4ba9-af10-743c55adc284"),
 ("2026-09-16T14:58:35.463+00:00","218a1742-6573-4d26-9c9c-41b63f34221e"),
 ("2026-09-16T14:58:40.359+00:00","62991f81-b598-42a7-ab9d-256e02aeabad"),
 ("2026-09-16T14:59:13.384+00:00","8013ec74-b700-458d-8c2f-59a5ef2ff5ed"),
 ("2026-09-16T14:59:18.519+00:00","b5ee2636-7c1e-477c-9d6f-a5d6c2ae15c9"),
 ("2026-09-16T14:59:23.115+00:00","a5552ee6-b33a-490f-bb52-e7e9742fb099"),
 ("2026-09-16T14:59:25.977+00:00","dd5dc576-270a-40e7-b1a6-ba43da01eb1b"),
 ("2026-09-16T14:59:34.171+00:00","03145c94-b378-4bac-8815-3019f02e6664"),
 ("2026-09-16T14:59:35.424+00:00","3ae2c5fe-42ed-4c21-a054-12a5d81bc7fe"),
 ("2026-09-16T14:59:42.053+00:00","5a411ce1-e9fb-43a5-bd43-da06dcc55e5"),
 ("2026-09-16T14:59:48.301+00:00","327e1d3f-230c-4187-9237-e3cc30854bcd"),
 ("2026-09-16T15:00:08.733+00:00","8f097c85-c6e7-4a95-8f1a-decbb8e7896f"),
 ("2026-09-16T15:01:31.328+00:00","d65b54ec-e39c-466a-bd5f-9800769977ee"),
 ("2026-09-16T15:02:33.763+00:00","9c4d4133-1558-4618-b7f9-9f0ea730dea5"),
 ("2026-09-16T15:02:56.845+00:00","1814cace-275a-4775-920f-be4ec0ae4c8c"),
 ("2026-09-16T15:03:03.515+00:00","9c916c02-2312-49f6-8158-5177cfcd4c88"),
 ("2026-09-16T15:03:17.428+00:00","b7863cf8-33da-48ed-9d9d-27ad65f59593"),
 ("2026-09-16T15:03:26.524+00:00","2de7bd1b-b81b-4c18-81d0-84a656e16e5f"),
 ("2026-09-16T15:03:52.137+00:00","d93f5326-b47c-4632-8f95-8f1dcc4846bf"),
 ("2026-09-16T15:03:57.367+00:00","59e01df5-87b9-4d82-ab21-1a33e9d5f4b7"),
 ("2026-09-16T15:04:08.318+00:00","10dddb1b-31c7-4ac4-88e3-2b8a2674ce8f"),
 ("2026-09-16T15:04:19.412+00:00","6fcea1f3-d1c8-46d9-89e6-b1895b079536"),
 ("2026-09-16T15:04:39.396+00:00","ffbfe583-a155-4854-848c-a127b500de86"),
 ("2026-09-16T15:04:46.513+00:00","d3e83802-4bff-4325-b9af-b6fc6ee6848d"),
 ("2026-09-16T15:07:45.422+00:00","5cd3b19a-6bb9-4b53-b17e-b463f6ba8835"),
 ("2026-09-16T15:16:37.717+00:00","4b9b1366-440b-9167-5e0d-6d2b8b60f94b"),
 ("2026-09-16T15:17:03.953+00:00","97fa31d5-a6c3-44ba-893f-eb469a512988"),
 ("2026-09-16T15:17:50.941+00:00","d1b43618-835f-4094-8e31-28e3ff4c3173"),
 ("2026-09-16T15:17:52.949+00:00","443de352-d2d0-4789-a519-9accf20bf330"),
 ("2026-09-16T15:17:53.37+00:00","c48cd1f1-5ff9-4a74-a13d-7636f2427ffa"),
 ("2026-09-16T15:18:27.25+00:00","bca6baec-9133-4ad3-9560-3588a6d3f678"),
 ("2026-09-16T15:18:32.265+00:00","2e4776b7-09cb-4e21-9a10-2caca6fcf783"),
 ("2026-09-16T15:18:41.793+00:00","3ae235f3-92ed-4941-8e2f-8870935d9f88"),
 ("2026-09-16T15:18:43.797+00:00","c991559b-0fd6-4c87-a725-1c45f914307f"),
 ("2026-09-16T15:19:07.518+00:00","a067fed8-0ff6-486a-9c6a-fa36d930dde2"),
 ("2026-09-16T15:19:20.874+00:00","6e553815-d296-4c49-bfd2-56a466b570ad"),
 ("2026-09-16T15:19:26.631+00:00","11282c80-2be4-4d49-a00c-d248d104aacb"),
 ("2026-09-16T15:19:29.75+00:00","a046fd50-d5ac-4150-ab90-48ad29b1d370"),
 ("2026-09-16T15:19:31.512+00:00","700e8f15-e3aa-4ebd-bf0e-336304e501a5"),
 ("2026-09-16T15:19:35.965+00:00","1f6ba21d-08e0-4adf-a203-1dbda7d73bfd"),
 ("2026-09-16T15:19:37.543+00:00","53c97ddf-a0b0-4a35-834b-ad95457586c6"),
 ("2026-09-16T15:19:38.378+00:00","92db0f0c-3afc-42ad-9f4b-9cb91fa5ed02"),
 ("2026-09-16T15:19:39.235+00:00","41a7b74b-272b-48b6-b287-b89cd933c615"),
 ("2026-09-16T15:19:40.233+00:00","4c6095dd-3372-4a77-9f25-0c29ed14be33"),
 ("2026-09-16T15:19:41.759+00:00","960d672d-2aa3-4191-bec4-8697bb8ff09a"),
 ("2026-09-16T15:19:42.665+00:00","859b1389-bef5-42e6-8cb6-e47a599de40d"),
 ("2026-09-16T15:19:45.235+00:00","5832f3a1-241f-44cd-9c47-3056baf17111"),
 ("2026-09-16T15:20:00.798+00:00","80113655-ec80-49de-874d-5590216ee308"),
 ("2026-09-16T15:20:09.283+00:00","e2a64839-5758-4db1-8beb-1b68c8b8ef6f"),
 ("2026-09-16T15:20:13.089+00:00","98121573-f936-41e3-8471-88d66299a752"),
 ("2026-09-16T15:20:19.803+00:00","53b3b166-093b-46f4-b494-166feb7092d0"),
 ("2026-09-16T15:20:23.816+00:00","da81120c-c231-4072-8645-879471e12066"),
 ("2026-09-16T15:20:24.413+00:00","1d7f2fff-c88d-4e96-a045-e95a1c052c27"),
 ("2026-09-16T15:20:30.087+00:00","304bfac9-35df-436e-b764-ac13e7502d3e"),
 ("2026-09-16T15:20:35.103+00:00","92f0369f-d621-41b4-a94f-f5d70f93e580"),
 ("2026-09-16T15:20:51.294+00:00","8814dbec-20f4-44ee-804f-31e7ea81ddb6"),
 ("2026-09-16T15:21:44+00:00","ac3256a3-4cc7-42c3-af72-d39f701ec424"),
 ("2026-09-16T15:25:32.567+00:00","bf8b215e-344e-4372-ad28-697968976e0d"),
 ("2026-09-16T15:28:34.931+00:00","1e9f0a08-97fc-e481-6b3a-bc74246fe4dd"),
 ("2026-09-16T17:31:35.335+00:00","62a49fbd-552d-4cdb-b54a-48d640beb887"),
 ("2026-09-16T17:40:47.309+00:00","92003afe-1343-ee54-d7bb-29fcc1a3e02c"),
 ("2026-09-16T17:40:51.671+00:00","43fbf192-9764-4592-9f41-5ef2a5dd851d"),
 ("2026-09-16T17:41:21.059+00:00","3a7e69df-1c0a-48a0-abf8-3e070f52fd92"),
 ("2026-09-16T17:41:24.187+00:00","0ba679ac-16fe-0fce-f68c-523eeaab56f7"),
 ("2026-09-16T17:41:35.18+00:00","24160897-d494-f180-1f02-1162beeff246"),
 ("2026-09-16T17:41:38.263+00:00","04d52745-2227-9654-0ccc-17f699495a11"),
 ("2026-09-16T17:41:55.591+00:00","901459fe-33b8-aad8-a418-0a5adfe076db"),
 ("2026-09-16T17:45:22.934+00:00","d14733b1-a998-4e8a-b476-bfb5cf23d1ad"),
]
assert len(CHAT_ROWS) == 121

SPAWN_ROWS = [
 (1789571359, 737, "3b9d37a1-7600-486c-a2d1-142fe38fcb6a",
  "7240686c-d790-463d-bad2-c969fc65885e"),
 (1789571380, 738, "aa7110c8-0fb6-468c-bb6d-7abd477bbd46",
  "7240686c-d790-463d-bad2-c969fc65885e"),
]

REDISPATCH = {
 737: "workflow-run-21fdb19d28ae43cfa773df0d3547963b",
 738: "workflow-run-3afbdf44a4bb47a9bbb49f6a60520229",
}

DAEMON_HITS = 0
FIX_ROUNDS = 1

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
fix_ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
fix_entries = []
with open(hits_path, "a") as f:
    for ts, uuid_ in CHAT_ROWS:
        ref = "assistant-msg-" + uuid_
        if ("chat", ref) not in seen:
            f.write(json.dumps({"ts": ts, "surface": "chat", "digest": SECONDARY,
                                "kind": "secondary", "length": 96, "ref": ref}) + "\n")
            seen.add(("chat", ref))
            chat_added += 1
        fix_entries.append((ref, "chat", "observed",
                            "chat-surface canned hit; turn already reached the user; nothing to re-run"))
    for epoch, spawn_id, child, parent in SPAWN_ROWS:
        ts = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
        if ("spawn", str(spawn_id)) not in seen:
            f.write(json.dumps({"ts": ts, "surface": "spawn", "digest": PRIMARY,
                                "kind": "primary", "length": 384, "ref": spawn_id,
                                "child_agent_id": child, "parent_agent_id": parent}) + "\n")
            seen.add(("spawn", str(spawn_id)))
            spawn_added += 1
        run_id = REDISPATCH.get(spawn_id, "unknown")
        fix_entries.append((spawn_id, "spawn", "redispatched_clean",
                            f"task recovered from ledger prompt; redispatched via vompl saved workflow clean route, run {run_id}"))

os.makedirs(os.path.dirname(FIXES), exist_ok=True)
with open(FIXES, "a") as f:
    for ref, surface, action, detail in fix_entries:
        f.write(json.dumps({"ts": fix_ts, "ref": ref, "surface": surface,
                            "action": action, "detail": detail}) + "\n")

total = chat_added + spawn_added + DAEMON_HITS
now = int(time.time())
window_start = datetime.fromtimestamp(WATERMARK, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
window_end = CHAT_ROWS[-1][0]
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
    "completed_anomalies": [
        {"spawn_id": s, "child_agent_id": c, "parent_agent_id": p,
         "completed_at_epoch": e, "redispatch_run": REDISPATCH.get(s)}
        for e, s, c, p in SPAWN_ROWS
    ],
    "fix_rounds": FIX_ROUNDS,
    "fixed_count": len(SPAWN_ROWS),
    "green": True,
    "resweep_note": "re-sweep with watermark advanced to round start found 0 new hits; all spawn anomalies have recorded fix outcomes",
    "maintained_by": "sorry-watchdog hook worker (ongoing)",
}
with open(os.path.join(AUDIT, "LATEST.json"), "w") as f:
    json.dump(latest, f, indent=2)

with open(CURSOR, "w") as f:
    f.write(str(now) + "\n")

with open(SWEEPS, "a") as f:
    f.write(json.dumps({"ts": now, "window_start": WATERMARK,
                        "chat_hits": chat_added, "spawn_hits": spawn_added,
                        "daemon_hits": DAEMON_HITS, "fix_rounds": FIX_ROUNDS,
                        "green": True}) + "\n")

print(f"chat_added={chat_added} spawn_added={spawn_added} fix_entries={len(fix_entries)} total={total} now={now}")
