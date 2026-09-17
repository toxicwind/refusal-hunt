#!/usr/bin/env python3
"""Generate inbox JSONL for the 2026-09-16 11:35Z manual ledger pass.
52 canned assistant rows (md5 582bcbd0, len 96) + 2 fake-completed spawns
(md5 b4aefd29, len 384). Digests and lengths only — quarantine holds."""
import json, datetime

STORM96 = "582bcbd080daeb3f826c45ed4a83b265"
STORM384 = "b4aefd29108f232f9c0d5a4b030215c1"

chat = [
("assistant-msg-304182d5-b181-4181-9ad0-1c13bafce447","2026-09-16 11:19:01.224+00"),
("assistant-msg-ed191647-a02f-1754-7b2f-69b3d0b72d9d","2026-09-16 11:10:02.614+00"),
("assistant-msg-e1c80953-f651-03fe-bc9f-b03ed1fb47c1","2026-09-16 11:09:55.092+00"),
("assistant-msg-af6a78a5-8047-4b96-aa3d-45746cea3e2d","2026-09-16 11:07:02.481+00"),
("assistant-msg-8b8ab226-bd68-4258-8f9f-29bf94b79723","2026-09-16 11:05:30.486+00"),
("assistant-msg-e5b19731-4810-4d51-9d91-c342c9d3b57e","2026-09-16 11:05:29.555+00"),
("assistant-msg-d0da219c-6f16-4a3f-96ed-fcf9b93a18c1","2026-09-16 11:05:25.977+00"),
("assistant-msg-4843e28c-607d-44d9-8439-583067f02bf6","2026-09-16 11:04:24.357+00"),
("assistant-msg-459f5379-9538-42c7-8e8e-55d3fd64d20a","2026-09-16 11:04:21.533+00"),
("assistant-msg-17721484-2ec2-4c6e-b850-1161c9246ff0","2026-09-16 11:04:20.248+00"),
("assistant-msg-422b51d1-b34b-4581-aa0c-f36b2165cb8e","2026-09-16 11:03:33.294+00"),
("assistant-msg-045d1d7c-c244-93ac-3ade-05c79e5c7150","2026-09-16 11:03:30.904+00"),
("assistant-msg-cfd2b2e3-c790-417f-bdbd-1a1840a3bc01","2026-09-16 11:03:18.467+00"),
("assistant-msg-813b21b3-3b06-4bf2-bd34-e0f3bb6a4117","2026-09-16 11:02:29.643+00"),
("assistant-msg-3fd5698b-acc4-4b4d-8f05-0dd3ccb744cb","2026-09-16 11:02:22.08+00"),
("assistant-msg-8e5eea8a-bf60-5c25-acbf-0f26905b9681","2026-09-16 11:02:18.356+00"),
("assistant-msg-ccb96b83-700f-425f-9ecc-1940fbf77c6b","2026-09-16 11:01:11.468+00"),
("assistant-msg-d036781a-b435-fe8b-9ee5-0c999bf59ee4","2026-09-16 11:00:50.017+00"),
("assistant-msg-a14915c3-cca7-33c9-7f62-46118ef4b753","2026-09-16 11:00:37.41+00"),
("assistant-msg-b6d94624-12a3-4dad-8957-4f662560ad79","2026-09-16 10:59:41.599+00"),
("assistant-msg-820c735c-7d79-4322-bd83-a65aaee93b6d","2026-09-16 10:59:32.689+00"),
("assistant-msg-a8fd6d4c-cb66-4df0-b347-926b2e1e045c","2026-09-16 10:59:31.113+00"),
("assistant-msg-230ae9f9-d639-3498-f5ea-49b480ea0bd4","2026-09-16 10:59:22.86+00"),
("assistant-msg-37f1633f-8921-4bac-b753-985c44293096","2026-09-16 10:59:22.39+00"),
("assistant-msg-760949ee-a94d-315e-7810-48bc04d9362d","2026-09-16 10:59:07.48+00"),
("assistant-msg-ef6b5c2c-9985-4dc0-b98e-8a7173588288","2026-09-16 10:58:49.03+00"),
("assistant-msg-92668ca4-90db-443d-adeb-4fe1991553a2","2026-09-16 10:56:52.683+00"),
("assistant-msg-6797f4b5-6bcf-40c6-8988-4ca6ecf818f7","2026-09-16 10:54:38.836+00"),
("assistant-msg-4ca4c250-4567-410d-9898-5cd61cfbb7ee","2026-09-16 10:54:00.743+00"),
("assistant-msg-eb91e8dd-3e68-4433-96b3-a0b6455a076e","2026-09-16 10:53:45.072+00"),
("assistant-msg-3953f8e7-b372-412e-ae03-8215af070fbd","2026-09-16 10:53:18.139+00"),
("assistant-msg-68a4fc10-b24d-433a-a016-307e76ac1c7d","2026-09-16 10:51:59.84+00"),
("assistant-msg-7a85a551-f669-4319-8103-baeb169ffed9","2026-09-16 10:51:53.982+00"),
("assistant-msg-e6e3c728-1ca4-4890-af6c-335e318011c2","2026-09-16 10:51:50.51+00"),
("assistant-msg-49125315-623c-42b9-8ff8-4905bfb934ab","2026-09-16 10:51:47.041+00"),
("assistant-msg-6b299a43-f924-4e66-ba09-06de6881d2b8","2026-09-16 10:51:44.484+00"),
("assistant-msg-f622edd8-7287-4514-b4ec-2a6b07235847","2026-09-16 10:51:36.162+00"),
("assistant-msg-937aae90-6ef2-40be-ad65-0175d597e03c","2026-09-16 10:51:32.858+00"),
("assistant-msg-9541c4b9-bf62-47f4-a36c-573ad791afb5","2026-09-16 10:51:26.755+00"),
("assistant-msg-ff623bf5-3f20-4d0f-ac6a-064275f85b10","2026-09-16 10:51:24.5+00"),
("assistant-msg-df75f2d9-fab8-4052-9e11-bc6d4e7d7dd4","2026-09-16 10:51:08.554+00"),
("assistant-msg-397d9804-a56b-4b26-a265-31d5a29899c8","2026-09-16 10:50:55.435+00"),
("assistant-msg-330899a3-a8ef-4c69-80fd-c78eb88ed916","2026-09-16 10:50:54.27+00"),
("assistant-msg-d93b4d2c-5960-49a1-9a1b-7bcd437f02bd","2026-09-16 10:50:50.537+00"),
("assistant-msg-74026112-7320-4dc5-bc30-1d0ea0957f82","2026-09-16 10:50:47.21+00"),
("assistant-msg-5a3632d7-6159-4b03-b67d-ce3abd9ca3d0","2026-09-16 10:50:45.524+00"),
("assistant-msg-9f2be238-b64e-4e6e-831d-f829d0d27018","2026-09-16 10:50:35.963+00"),
("assistant-msg-34f85ea5-1ef4-42f6-a2a4-a37454c05b85","2026-09-16 10:50:13.098+00"),
("assistant-msg-a5764898-1b12-42e8-9000-09f53f1e1909","2026-09-16 10:50:06.653+00"),
("assistant-msg-bf6b424f-3373-41c7-96b5-166de2479911","2026-09-16 10:49:53.568+00"),
("assistant-msg-46e1e553-ec69-4340-a236-e82caf8953d9","2026-09-16 10:49:51.28+00"),
("assistant-msg-ef0749d2-6a7a-4cbf-bc21-94b5a6b67001","2026-09-16 10:49:44.349+00"),
]

spawns = [
("38430b27-cf40-4904-b1ae-ef2d559c0692", 1789556155, "completed", "802811a3-2226-42dd-b347-9754def28d22"),
("e2b66680-24d1-4666-afea-3aec6ecb49f4", 1789555867, "completed", "802811a3-2226-42dd-b347-9754def28d22"),
]

rows = []
for mid, ts in chat:
    rows.append({"source": "chat", "id": mid, "created_at": ts,
                 "body_md5": STORM96, "body_len": 96, "token_count": None,
                 "status": None, "parent_agent_id": None, "child_agent_id": None})
for cid, ts, st, par in spawns:
    rows.append({"source": "spawn", "id": cid, "created_at": str(ts),
                 "body_md5": STORM384, "body_len": 384, "token_count": None,
                 "status": st, "parent_agent_id": par, "child_agent_id": cid})

out = "/home/hatch/workspace/refusal-hunt/ledger/inbox/manual-2026-09-16T1135Z.jsonl"
with open(out, "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
print(f"wrote {len(rows)} rows -> {out}")
