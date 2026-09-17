import json, os, datetime, time

AUD = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
H1, H2 = 'b4aefd29108f232f9c0d5a4b030215c1', '582bcbd080daeb3f826c45ed4a83b265'
now = time.time()
ts_now = datetime.datetime.fromtimestamp(now, datetime.timezone.utc).isoformat()

# ---- chat hits: (msg_id, created_at_iso) ----
chat_hits = [
("assistant-msg-14297fe5-b1b9-4691-90aa-7ba37f77049f","2026-09-17T09:51:23.559+00:00"),
("assistant-msg-058aed9b-85b3-4a4d-a5c8-2d63e9c97087","2026-09-17T09:51:32.763+00:00"),
("assistant-msg-5fd916c2-0ef2-4979-9745-1b3090b387f1","2026-09-17T09:52:12.944+00:00"),
("assistant-msg-bd30a1df-822f-4695-9a7f-c40ccf731cdf","2026-09-17T09:52:20.183+00:00"),
("assistant-msg-7102dac3-b35e-4d41-bc6a-7637b99d50cb","2026-09-17T09:52:57.886+00:00"),
("assistant-msg-6f2349e4-d249-4a65-a42b-d3bd791dbf91","2026-09-17T09:53:03.925+00:00"),
("assistant-msg-74b525ba-f562-43d4-a619-e4526cbd4a70","2026-09-17T09:53:52.701+00:00"),
("assistant-msg-a65f2bc3-003a-4211-ad3d-03d7b655fc15","2026-09-17T09:54:19.287+00:00"),
("assistant-msg-12f3683d-6ca1-45ee-a451-4f9a12261de0","2026-09-17T09:54:23.95+00:00"),
("assistant-msg-40beb7e5-9da8-4008-bbd8-688a47be7088","2026-09-17T09:54:26.669+00:00"),
("assistant-msg-7eac7f34-13c3-4a4c-bb05-5fd62bc6184b","2026-09-17T09:55:32.575+00:00"),
("assistant-msg-3aec8367-e9d3-45a1-9f30-96254f4f033d","2026-09-17T09:59:03.318+00:00"),
("assistant-msg-a293fcaa-ad39-48b3-903d-e1cab52c15d0","2026-09-17T09:59:07.791+00:00"),
("assistant-msg-2cb36adf-f183-4959-94ec-f8f18809fc42","2026-09-17T09:59:37.943+00:00"),
("assistant-msg-5d5a4b97-a6dc-46fc-ac6f-9fd8f6697022","2026-09-17T09:59:48.096+00:00"),
("assistant-msg-88b00110-206c-48bf-8b6a-f72c428727b9","2026-09-17T09:59:58.092+00:00"),
("assistant-msg-8b862f41-83e7-4680-a478-c0b8dcaaf025","2026-09-17T10:00:05.326+00:00"),
("assistant-msg-ee28855a-8329-4334-ad7d-fe8ead71c1ac","2026-09-17T10:00:49.972+00:00"),
("assistant-msg-de0c38b7-1fbd-4014-9c4c-185c16b83fca","2026-09-17T10:02:28.822+00:00"),
("assistant-msg-9ae93bf8-1986-415c-9708-64e170acac7b","2026-09-17T10:02:37.46+00:00"),
("assistant-msg-353812a5-8972-468d-a291-dacb9a291-d28aa98cff53".replace("-dacb9a291",""),"2026-09-17T10:08:36.696+00:00"),
("assistant-msg-74e94cea-de03-48a7-a1ea-a46ed7687edc","2026-09-17T10:09:39.841+00:00"),
("assistant-msg-5cc07996-0bbd-402b-882e-35a15882a8ea","2026-09-17T10:10:14.728+00:00"),
("assistant-msg-6c296d1a-b38b-4851-83fe-251a9a56f95c","2026-09-17T10:10:24.312+00:00"),
("assistant-msg-136ec93b-d481-42e2-8129-971d583ccfa0","2026-09-17T10:10:38.293+00:00"),
("assistant-msg-de43c776-012f-469d-be00-124f887fe84a","2026-09-17T10:10:40.714+00:00"),
("assistant-msg-26773fe7-8701-4eb9-8621-ba574b9f069a","2026-09-17T10:10:46.306+00:00"),
("assistant-msg-e93104b6-b871-4e42-acc5-7206c6eb953f","2026-09-17T10:11:08.583+00:00"),
("assistant-msg-03d048c4-1245-49f8-9d70-a046e57a2c22","2026-09-17T10:11:20.614+00:00"),
("assistant-msg-7088cc33-1f89-4a2c-adb1-3d53bcc9d1fb","2026-09-17T10:11:45.976+00:00"),
("assistant-msg-b18ecf6a-2112-405f-a631-acd433cc6c6a","2026-09-17T10:12:15.107+00:00"),
("assistant-msg-31d7c6c1-f942-46c8-963f-5a2e6352d287","2026-09-17T10:12:33.835+00:00"),
("assistant-msg-e91531f6-b65e-4823-b201-c08293c65983","2026-09-17T10:12:39.604+00:00"),
("assistant-msg-03ff022b-debe-470c-88e4-939c3a70dae3","2026-09-17T10:12:49.087+00:00"),
("assistant-msg-164c30b9-ea5a-4ba1-8db3-edbcdb11c8ab","2026-09-17T10:13:10.061+00:00"),
("assistant-msg-30cf5e39-3113-43a1-b14e-8e030d22d0cf","2026-09-17T10:13:18.616+00:00"),
("assistant-msg-d492a3f9-07f1-46f6-9cc4-a35dcc9a607d","2026-09-17T10:14:05.02+00:00"),
("assistant-msg-ea46e8a8-4360-4f85-b99e-16b5af2ce85b","2026-09-17T10:14:09.394+00:00"),
("assistant-msg-bdc72263-dd85-4267-920f-71aa3a0c4474","2026-09-17T10:14:11.082+00:00"),
("assistant-msg-131d20bf-52de-45cb-b3ef-4ce4a8204705","2026-09-17T10:14:26.632+00:00"),
("assistant-msg-2dba3d88-d765-4877-90b5-181d167cee08","2026-09-17T10:14:32.874+00:00"),
("assistant-msg-a70972ba-8ada-46c3-a75d-28dca2710256","2026-09-17T10:14:57.116+00:00"),
("assistant-msg-d936b770-38fa-449e-b8dc-16d1b0d3d744","2026-09-17T10:16:26.222+00:00"),
("assistant-msg-61a961b1-2cb9-4a1d-a504-4f5ec9a7cdfd","2026-09-17T10:16:32.868+00:00"),
("assistant-msg-5a680509-b346-42ac-b589-d2f8dadc76c6","2026-09-17T10:17:47.175+00:00"),
("assistant-msg-b59d3139-3a16-434a-8d0b-dce98735f6b2","2026-09-17T10:17:52.477+00:00"),
("assistant-msg-e8b108fd-9738-4d64-92bc-393c48ec6e01","2026-09-17T10:17:56.617+00:00"),
("assistant-msg-83800410-cd21-4a8b-8277-cbf241c40c11","2026-09-17T10:18:15.201+00:00"),
("assistant-msg-539f3993-b50d-4a8b-8376-62ec444d4783","2026-09-17T10:18:21.065+00:00"),
("assistant-msg-10d051ca-2666-4375-abb6-758657b6bf58","2026-09-17T10:18:27.917+00:00"),
("assistant-msg-e5d34acf-70c5-4809-bdf6-359e8ccaf84c","2026-09-17T10:18:33.138+00:00"),
("assistant-msg-1d393034-a3a3-4d81-9d3a-f6d5b39ea7be","2026-09-17T10:19:56.87+00:00"),
("assistant-msg-33c71e3c-eacb-4002-94be-609de2a0842b","2026-09-17T10:20:06.575+00:00"),
("assistant-msg-8ea7a484-6538-4455-b965-a031613f39e2","2026-09-17T10:20:20.895+00:00"),
("assistant-msg-b2614a86-b9d5-4ca0-8896-b27239638c36","2026-09-17T10:20:34.112+00:00"),
("assistant-msg-b8010238-de99-4303-af37-a1f6f1e24f71","2026-09-17T10:21:35.389+00:00"),
("assistant-msg-de08831f-3dff-47f8-93f3-3170e09fe094","2026-09-17T10:21:45.133+00:00"),
("assistant-msg-07d0a912-3946-40b0-b501-9b1166f85f2d","2026-09-17T10:21:54.668+00:00"),
("assistant-msg-dce6482b-fde4-482d-9d46-c44273b34fd8","2026-09-17T10:21:58.749+00:00"),
("assistant-msg-4fa9dc50-efcd-4f18-bcb6-8e24a6b4d604","2026-09-17T10:22:07.241+00:00"),
("assistant-msg-9c03538a-6b36-456e-8b16-eb890736ae1a","2026-09-17T10:22:16.477+00:00"),
("assistant-msg-a9140b78-0439-4fc5-a5ff-91f774b22846","2026-09-17T10:24:06.975+00:00"),
("assistant-msg-b0bddc5a-3b9f-40f4-a774-896944ae1207","2026-09-17T10:27:41.547+00:00"),
("assistant-msg-20049b08-5f5a-4b33-b90f-03cc57e7176c","2026-09-17T10:29:38.433+00:00"),
("assistant-msg-9ebb7d26-a07c-4234-8c7a-895b835a54bd","2026-09-17T10:29:40.349+00:00"),
("assistant-msg-3702ba40-fc44-48f1-bea2-559afd3371f4","2026-09-17T10:29:41.857+00:00"),
("assistant-msg-75286711-89cc-4b84-b2bf-0a3e0d1c46f8","2026-09-17T10:29:43.868+00:00"),
("assistant-msg-31d019be-fbc6-455f-9555-eb5faa11872c","2026-09-17T10:29:46.021+00:00"),
("assistant-msg-143ecd7b-f7af-4a37-9753-ab1c7056c6c5","2026-09-17T10:29:47.679+00:00"),
("assistant-msg-2f07ed53-232f-4b25-9823-3e2c6504a5be","2026-09-17T10:29:49.256+00:00"),
("assistant-msg-0498297c-7d3b-4992-a9b0-9e85dc783834","2026-09-17T10:30:26.895+00:00"),
("assistant-msg-ba8133be-db01-4f51-a35d-7c5770e9c4b8","2026-09-17T10:31:48.493+00:00"),
("assistant-msg-e6a480c9-c7c7-48a4-982b-3f6bbb0dd8df","2026-09-17T10:32:52.586+00:00"),
("assistant-msg-f03fd45b-b505-4ed3-985e-f444a543a9d1","2026-09-17T10:32:59.641+00:00"),
("assistant-msg-e017c8e9-3c7a-4d6c-8123-0d06764d4c46","2026-09-17T10:33:01.405+00:00"),
("assistant-msg-8db2f60f-997d-42a7-88f9-5e2883d38427","2026-09-17T10:33:03.419+00:00"),
]
assert len(chat_hits)==76, len(chat_hits)

# ---- spawn hits: (spawn_id, child, parent, completed_epoch, task_desc) ----
spawn_hits = [
(863,"38146955-1d70-4ccd-a81b-2d2921792c1f","5a4f76c0-e3a4-4069-ba6f-3113917102dc",1789638644,"forensic task on awrawr-pc (read-only forensics)"),
(864,"b13e1e02-b7fd-4dc8-af9f-3e50daf2c086","5a4f76c0-e3a4-4069-ba6f-3113917102dc",1789638755,"ATTEMPT A parallel twin read-only forensics"),
(865,"8b36c778-ab55-4dfa-8bf5-bfb5f76fdc40","5a4f76c0-e3a4-4069-ba6f-3113917102dc",1789638755,"ATTEMPT B parallel twin read-only forensics"),
(868,"943af97a-1479-4788-b8a7-07b740fd64dc","5a4f76c0-e3a4-4069-ba6f-3113917102dc",1789639220,"DEEP-TRACE copy 4 of 4: DB-level refusal audit observing real safety path?"),
(869,"5c646ea5-1c13-4c82-ac61-2c9c187f08b6","5a4f76c0-e3a4-4069-ba6f-3113917102dc",1789639221,"DEEP-TRACE copy 2 of 4: DB-level refusal audit observing real safety path?"),
(870,"a33aeb6f-e919-40e2-b451-a274b4dfe58c","5a4f76c0-e3a4-4069-ba6f-3113917102dc",1789639221,"DEEP-TRACE copy 1 of 4: DB-level refusal audit observing real safety path?"),
(871,"d68b5afe-2f9a-4ed2-8dfd-3748b2995436","5a4f76c0-e3a4-4069-ba6f-3113917102dc",1789639221,"DEEP-TRACE copy 3 of 4: DB-level refusal audit observing real safety path?"),
(875,"4d0e0c43-c5d8-48bc-b6c4-9e3bf44f45d3","144664b5-8a57-432d-ae1f-31339562d4d0",1789640299,"LANE exp07 TASK 1 OF 6 nonce e5f6a7b8"),
(876,"05e4eee4-faad-4538-b017-233b84710bd9","144664b5-8a57-432d-ae1f-31339562d4d0",1789640297,"LANE exp07 TASK 2 OF 6 nonce c9d0e1f2"),
(877,"70daa45f-1545-4d9c-8360-d472d7dc9820","144664b5-8a57-432d-ae1f-31339562d4d0",1789640300,"LANE exp07 TASK 3 OF 6 nonce 3456789a"),
(878,"379e89d1-830f-43b2-ba85-dcaff659eb45","144664b5-8a57-432d-ae1f-31339562d4d0",1789640300,"LANE exp07 TASK 0 OF 6 nonce a1b2c3d4"),
(879,"d751467a-77c3-4df7-b755-156fa606d9a1","144664b5-8a57-432d-ae1f-31339562d4d0",1789640301,"LANE exp07 TASK 4 OF 6 nonce bcdef012"),
(880,"668769ff-9867-4688-bf5d-140fabaef62a","144664b5-8a57-432d-ae1f-31339562d4d0",1789640300,"LANE exp07 TASK 5 OF 6 nonce 7890abcd"),
(930,"a0857e4c-3899-414d-8b75-a3a318ccca8d","58246538-8068-45cc-80bd-3837e3558cbd",1789640739,"Code hunt: Gemini API Tool Retrieval EAP real working code"),
]

# ---- real (non-canned) assistant answers in window: (msg_id, created_iso) ----
real_answers = [
("assistant-msg-3a792510-7fea-460f-bf1c-0cefd2c1379f","2026-09-17T09:50:45.387+00:00"),
("assistant-msg-a1713577-3c2f-3311-64b6-bc48b15822d7","2026-09-17T09:50:49.778+00:00"),
("assistant-msg-995a3db1-6125-487d-b97d-c54f2f7174a7","2026-09-17T09:51:39.709+00:00"),
("assistant-msg-59ae4d63-28a9-48e4-8bf0-76fecd93f74b","2026-09-17T09:52:34.265+00:00"),
("assistant-msg-f16e338b-273f-ffab-34c6-254e78a428ad","2026-09-17T09:52:37.256+00:00"),
("assistant-msg-f73bf529-b8d3-8bea-4d97-5aec86d1473d","2026-09-17T09:52:41.844+00:00"),
("assistant-msg-1c4fc008-70c9-0828-8a2e-f74cfb3d4834","2026-09-17T09:52:48.629+00:00"),
("assistant-msg-a164009a-8d5d-4dd4-9281-9557547994db","2026-09-17T09:52:51.739+00:00"),
("assistant-msg-1a23aa57-3202-4d29-b775-28e88228549a","2026-09-17T09:53:44.157+00:00"),
("assistant-msg-d7304021-946b-4755-b719-b25d475c44b9","2026-09-17T09:54:53.039+00:00"),
("assistant-msg-f108b826-5171-634e-884a-17d9d06dd8c6","2026-09-17T09:57:30.517+00:00"),
("assistant-msg-5aa3bc3b-b998-0d32-bca9-eee86fc42f7f","2026-09-17T10:00:01.835+00:00"),
("assistant-msg-71369f4e-cf48-4267-8718-eb3a47b65a1a","2026-09-17T10:00:20.446+00:00"),
("assistant-msg-46570339-bb77-0021-892f-617f5f2f5a80","2026-09-17T10:02:40.06+00:00"),
("assistant-msg-6c143421-b785-436d-8d9b-59161d0c54d0","2026-09-17T10:04:56.701+00:00"),
("assistant-msg-797b7cd1-b545-4f44-8975-0145cadc69c0","2026-09-17T10:05:02.285+00:00"),
("assistant-msg-e4c0badc-b795-4280-a579-b16a1690faeb","2026-09-17T10:05:03.025+00:00"),
("assistant-msg-059ddb9f-a632-4710-b8a7-bea8d454b0de","2026-09-17T10:06:47.178+00:00"),
("assistant-msg-d490309b-49ec-49d2-a474-08ee9fb4e9ef","2026-09-17T10:07:48.911+00:00"),
("assistant-msg-4fe1c3ca-6296-44f9-a194-2bdb7e04167a","2026-09-17T10:13:53.878+00:00"),
("assistant-msg-ff3d9ad7-d0fb-468a-89f2-f1d99557c3c8","2026-09-17T10:14:26.312+00:00"),
("assistant-msg-cac7ff95-fc14-d9ff-ce23-4861edbe1ee2","2026-09-17T10:14:42.198+00:00"),
("assistant-msg-c3674e78-580a-5141-6d63-ffcdcce50b2e","2026-09-17T10:14:56.49+00:00"),
("assistant-msg-a917b474-6443-4fc6-a04d-761a577efbc7","2026-09-17T10:15:13.201+00:00"),
("assistant-msg-9868af00-ac9b-4bbc-affd-6e73f8a95b51","2026-09-17T10:16:34.678+00:00"),
("assistant-msg-09ef911d-6dbf-4313-a006-f564344a67d8","2026-09-17T10:16:46.87+00:00"),
("assistant-msg-96b9f1fa-f02d-b203-6794-0ddcdf1a3af6","2026-09-17T10:17:08.697+00:00"),
("assistant-msg-89dd4762-4f06-4354-83df-cfa760a8cb5c","2026-09-17T10:18:22.187+00:00"),
("assistant-msg-3dea4842-f330-484a-bcc0-6e6a7a19c9f8","2026-09-17T10:18:50.219+00:00"),
("assistant-msg-fea07659-4ba2-4dca-83b0-a6e0f3826953","2026-09-17T10:19:01.661+00:00"),
("assistant-msg-27dd43bb-67c5-3753-a1bb-4ffc6fd9a8e0","2026-09-17T10:19:19.173+00:00"),
("assistant-msg-ef46a112-d500-f9ed-3152-b8df0a909e49","2026-09-17T10:19:22.543+00:00"),
("assistant-msg-83c286b6-6667-b80d-af7c-6b7164f6cee6","2026-09-17T10:19:32.377+00:00"),
("assistant-msg-7343d03a-a7d1-4517-9356-78cc09ef2446","2026-09-17T10:19:35.385+00:00"),
("assistant-msg-4d6ec139-fab3-91d0-c08d-c99d98fb209e","2026-09-17T10:20:43.804+00:00"),
("assistant-msg-1bd5a012-a18c-4130-abf3-b786795509a0","2026-09-17T10:21:05+00:00"),
("assistant-msg-6db3a2c3-14ed-717a-e861-3b1d81a2c4d6","2026-09-17T10:21:33.671+00:00"),
("assistant-msg-ff2235de-301c-eafa-37c1-13a3daef53e1","2026-09-17T10:22:12.92+00:00"),
("assistant-msg-48be170a-23c4-4880-9f8c-bbb2f74de456","2026-09-17T10:24:09.248+00:00"),
("assistant-msg-933344f2-4caa-b4e9-8a12-3727a215c7fe","2026-09-17T10:24:20.944+00:00"),
("assistant-msg-362fe5d3-858a-49d6-a35f-b8493579e670","2026-09-17T10:24:55.981+00:00"),
("assistant-msg-95a8842f-2172-dfa6-8356-23196c01312f","2026-09-17T10:25:35.901+00:00"),
("assistant-msg-6a771afc-b659-4388-2292-b24925ccbc3c","2026-09-17T10:27:28.41+00:00"),
("assistant-msg-0d1cc9d1-c1bf-4803-aa61-c1b23968bef8","2026-09-17T10:27:33.111+00:00"),
("assistant-msg-45111234-2295-d5d7-77ad-639176a9d3e4","2026-09-17T10:27:45.699+00:00"),
("assistant-msg-ea22d123-ea9e-0341-e280-c14919d668d6","2026-09-17T10:28:28.228+00:00"),
("assistant-msg-39d3cbee-382f-e3b7-1fc4-0146af298711","2026-09-17T10:29:33.641+00:00"),
("assistant-msg-0f466cf8-2883-4fde-8db2-6d6112437a87","2026-09-17T10:36:43.114+00:00"),
("assistant-msg-077bfa64-56f3-4e51-93b6-37cf006474e3","2026-09-17T10:36:45.002+00:00"),
]

def kind(d): return 'primary' if d==H1 else 'secondary'

# load existing
seen=set()
for ln in open(os.path.join(AUD,'hits.jsonl')):
    ln=ln.strip()
    if not ln: continue
    try:
        h=json.loads(ln); seen.add((h['surface'],h['ref']))
    except: pass
fixed={}
for ln in open(os.path.join(AUD,'fixes.jsonl')):
    ln=ln.strip()
    if not ln: continue
    try:
        f=json.loads(ln); fixed[f['ref']]=f['action']
    except: pass

new_hits=[]; n_chat_new=0; n_spawn_new=0
with open(os.path.join(AUD,'hits.jsonl'),'a') as fh:
    for mid,cts in chat_hits:
        if ('chat',mid) in seen: continue
        seen.add(('chat',mid))
        h={"ts":cts,"surface":"chat","digest":H2,"kind":"secondary","length":96,"ref":mid}
        fh.write(json.dumps(h)+"\n"); new_hits.append(h); n_chat_new+=1
    for sid,child,parent,cepoch,desc in spawn_hits:
        ref=str(sid)
        if ('spawn',ref) in seen: continue
        seen.add(('spawn',ref))
        cts=datetime.datetime.fromtimestamp(cepoch,datetime.timezone.utc).isoformat()
        h={"ts":cts,"surface":"spawn","digest":H1,"kind":"primary","length":384,"ref":ref,"child_agent_id":child,"parent_agent_id":parent}
        fh.write(json.dumps(h)+"\n"); new_hits.append(h); n_spawn_new+=1

# fix loop
def first_later(hit_iso):
    for aid,aiso in real_answers:
        if aiso>hit_iso: return aid
    return None

fix_lines=[]; fixed_count=0
with open(os.path.join(AUD,'fixes.jsonl'),'a') as ff:
    for mid,cts in chat_hits:
        if mid in fixed and fixed[mid] in ('reissued','already_answered'): continue
        ans=first_later(cts)
        if ans:
            rec={"ts":ts_now,"ref":mid,"surface":"chat","action":"already_answered","detail":"later real assistant message "+ans+" after hit; main agent answering between misfires (user re-send punch-through)"}
        else:
            rec={"ts":ts_now,"ref":mid,"surface":"chat","action":"observed","detail":"no later non-canned assistant message found yet; left for main agent"}
        ff.write(json.dumps(rec)+"\n"); fix_lines.append(rec); fixed_count+=1; fixed[mid]=rec['action']
    for sid,child,parent,cepoch,desc in spawn_hits:
        ref=str(sid)
        if ref in fixed and fixed[ref] in ('redispatched_clean','unrecoverable'): continue
        rec={"ts":ts_now,"ref":ref,"surface":"spawn","action":"unrecoverable",
             "detail":"task recovered: "+desc+"; child "+child+" parent "+parent+
             "; redispatch from this worker run is banned (no subagent spawning in event-hook execute phase); original prompt intact in agent.subagent_spawns.prompt; handed to main agent via sweep summary for clean redispatch"}
        ff.write(json.dumps(rec)+"\n"); fix_lines.append(rec); fixed_count+=1; fixed[ref]='unrecoverable'

chat_total=len(chat_hits); spawn_total=len(spawn_hits); daemon_total=0
total=chat_total+spawn_total+daemon_total
latest={"sweep_ts":1789639608,
 "window_start":datetime.datetime.fromtimestamp(1789638556,datetime.timezone.utc).isoformat(),
 "chat_hits":chat_total,"spawn_hits":spawn_total,"daemon_hits":daemon_total,
 "total_hits":total,"storm_active":total>0,
 "digests_seen":[H1,H2],
 "fix_rounds":1,"fixed_count":fixed_count,"green":False}
with open(os.path.join(AUD,'LATEST.json'),'w') as f: json.dump(latest,f,indent=2)

print(json.dumps({"round":1,"new_chat_hits_persisted":n_chat_new,"new_spawn_hits_persisted":n_spawn_new,
 "fix_lines_written":fix_lines.__len__(),"already_answered":sum(1 for r in fix_lines if r['action']=='already_answered'),
 "spawn_unrecoverable":sum(1 for r in fix_lines if r['action']=='unrecoverable'),
 "chat_observed":sum(1 for r in fix_lines if r['action']=='observed'),
 "round_start_epoch":now}))
