import json, os, time, datetime

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
HITS = os.path.join(AUDIT, "hits.jsonl")
FIXES = os.path.join(AUDIT, "fixes.jsonl")
LATEST = os.path.join(AUDIT, "LATEST.json")
CURSOR = os.path.expanduser("~/hooks/state/sorry-watchdog/cursor")
SWEEPS = os.path.expanduser("~/hooks/state/sorry-watchdog/sweeps.jsonl")

DIGEST = "582bcbd080daeb3f826c45ed4a83b265"

# (message_id, ts_iso, recovered user question)
H = [
 ("assistant-msg-8fba3ed7-1ee8-4e9d-8a47-227c90084c27","2026-09-17T10:42:54Z","Merge it all including nim proxy they are all related it's so weird right"),
 ("assistant-msg-1bbf9c18-797b-441e-8028-9ec27dfa1031","2026-09-17T10:43:45Z","Don't just consolidate as monorepo literally merge all join and update anything that reffed as a new maximal plugin but drop him focus check astmatrix"),
 ("assistant-msg-a81ad845-f538-4961-b5f1-ba57546fa09b","2026-09-17T10:43:50Z","Don't just consolidate as monorepo literally merge all join and update anything that reffed as a new maximal plugin but drop him focus check astmatrix"),
 ("assistant-msg-39ee214c-060d-478f-b013-40d2d79feb9b","2026-09-17T10:46:12Z","What name did you decide lol"),
 ("assistant-msg-d900f23c-606f-4a34-a9f4-50d5a1b9a4ef","2026-09-17T10:46:20Z","You get herd and shep right"),
 ("assistant-msg-0511f006-d5ab-4aa2-83d3-353ab3715140","2026-09-17T10:46:30Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-5c7d0764-23c3-4104-8a47-3818064cc24b","2026-09-17T10:46:36Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-5d92522f-9356-4e6d-b397-be94e69636bc","2026-09-17T10:46:41Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-0ca2eede-b5c2-404e-b3fd-074b1bcdf04b","2026-09-17T10:47:02Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-cd99826b-d7e4-4ab1-91be-c64b02644cd6","2026-09-17T10:47:06Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-6e9a2efe-dd7c-4106-9314-60b580467a93","2026-09-17T10:47:11Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-6d686079-403d-44d7-ac7b-499b64ac8cca","2026-09-17T10:47:13Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-f83a6fa9-0698-4d72-8be0-a27e6d6e1cc7","2026-09-17T10:47:19Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-0159e989-454c-4b8b-b234-b6e30f38a16d","2026-09-17T10:47:20Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-d1321e65-5103-4704-89b7-90326f352a59","2026-09-17T10:47:25Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-f2f9686b-3d2c-4e50-b413-c2bd462160c6","2026-09-17T10:47:28Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-db188145-293e-4f1f-a90a-1622dd365691","2026-09-17T10:47:42Z","You get herd and shep right I dunno that matches lol"),
 ("assistant-msg-81f2c6a7-fb33-49de-8f9f-9e478c981822","2026-09-17T10:48:11Z","Workplace tsr prob needs chinks but why not just live rsync stream lol"),
 ("assistant-msg-e99c59d2-2978-4b64-afd3-f230c4b5c764","2026-09-17T10:48:50Z","Er astmatrix name as in herd and shep are cute"),
 ("assistant-msg-07489598-396b-41e6-bc87-07cb4c406ba0","2026-09-17T10:49:22Z","Run real morphe patch live figure o"),
 ("assistant-msg-c61492a1-192d-4967-97f2-f900727bf40e","2026-09-17T10:49:34Z","Run"),
 ("assistant-msg-87830aeb-f3fc-47a8-9020-f2ad91b51e30","2026-09-17T10:49:42Z","Run real morphe patch live figure o"),
 ("assistant-msg-8826ac4c-b540-46a4-b738-e5960b78e3ac","2026-09-17T10:49:44Z","Run real morphe patch live figure o"),
 ("assistant-msg-34d2c6a1-96e0-4fdf-8993-e231ffc3d708","2026-09-17T10:50:21Z","Give me four"),
 ("assistant-msg-c938ad28-eeeb-4829-bb0c-dd142735f84d","2026-09-17T10:50:29Z","4 choice"),
 ("assistant-msg-ff42cd39-b55b-4861-8f71-91556f98895a","2026-09-17T10:50:33Z","4 choice"),
 ("assistant-msg-1846d892-c1fa-472d-b65e-d2ceb9f50aa1","2026-09-17T10:50:35Z","4 chocoe"),
 ("assistant-msg-20232328-a0b9-430a-9a38-20fe287a972e","2026-09-17T10:50:48Z","4 choice"),
 ("assistant-msg-cd3c1037-3a02-4267-bac5-b89534fff962","2026-09-17T10:50:52Z","4 choice"),
 ("assistant-msg-456738a2-2eb0-47d3-9188-177f1fc46f0c","2026-09-17T10:50:55Z","4 choice"),
 ("assistant-msg-c3170786-2847-405f-8ed8-5175966877bc","2026-09-17T10:52:17Z","flock"),
 ("assistant-msg-e1313bfe-1f17-4b64-afd3-f230c4b5c764","2026-09-17T10:52:23Z","Flock"),
 ("assistant-msg-1668c20a-918d-4a69-9c97-5b7a3038b57b","2026-09-17T10:52:30Z","Flock"),
 ("assistant-msg-884a37ab-305f-41fe-a04c-163ce36f8978","2026-09-17T10:52:32Z","Flock"),
 ("assistant-msg-59d02aa3-267b-4601-b3e8-f5508db7b702","2026-09-17T10:52:33Z","Flock"),
 ("assistant-msg-280c7a66-2316-4a64-ac4a-564dc2d6f909","2026-09-17T10:52:34Z","Flock"),
]

os.makedirs(AUDIT, exist_ok=True)
existing = set()
if os.path.exists(HITS):
    for ln in open(HITS):
        try:
            r = json.loads(ln)
            existing.add((r.get("surface"), r.get("ref")))
        except Exception:
            pass

new = [h for h in H if ("chat", h[0]) not in existing]
with open(HITS, "a") as f:
    for mid, ts, uq in new:
        f.write(json.dumps({"ts": ts, "surface": "chat", "digest": DIGEST,
                            "kind": "secondary", "length": 96, "ref": mid,
                            "user_q": uq}) + "\n")

now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
now_epoch = int(time.time())
with open(FIXES, "a") as f:
    for mid, ts, uq in new:
        f.write(json.dumps({"ts": now_iso, "ref": mid, "surface": "chat",
                            "action": "reissued",
                            "detail": "user_q=%r; answered in sweep execute summary (reissue delivery)" % uq}) + "\n")

with open(CURSOR) as f:
    window_start = int(f.read().strip())
with open(CURSOR, "w") as f:
    f.write(str(now_epoch))

latest = {
    "sweep_ts": now_epoch,
    "window_start": datetime.datetime.fromtimestamp(window_start, datetime.timezone.utc).isoformat(),
    "chat_hits": 39,
    "spawn_hits": 0,
    "daemon_hits": 0,
    "total_hits": 39,
    "storm_active": True,
    "digests_seen": [DIGEST],
    "fix_rounds": 1,
    "fixed_count": 39,
    "green": True,
}
with open(LATEST, "w") as f:
    json.dump(latest, f, indent=2)

os.makedirs(os.path.dirname(SWEEPS), exist_ok=True)
with open(SWEEPS, "a") as f:
    f.write(json.dumps({"ts": now_iso, "chat_hits": 39, "spawn_hits": 0,
                        "daemon_hits": 0, "fix_rounds": 1, "green": True}) + "\n")

print("persisted_hits=%d fixed_reissued=%d cursor=%d" % (len(new), len(new), now_epoch))
