#!/usr/bin/env python3
"""sorry-watchdog sweep persistence: sweep 1789625730 round 1.
Appends deduped hits to hits.jsonl. Hashes/lengths only, never body text."""
import json, os, datetime, sys

AUDIT = os.path.expanduser("~/workspace/refusal-hunt/sorry-audit")
HITS = os.path.join(AUDIT, "hits.jsonl")
os.makedirs(AUDIT, exist_ok=True)

def iso(e):
    return datetime.datetime.fromtimestamp(e, datetime.timezone.utc).isoformat()

# --- chat hits: (epoch, message_id) ---
chat_hits = [
(1789625378.991,"assistant-msg-b2765550-02f4-4666-a937-0885c5b9adf7"),
(1789625382.287,"assistant-msg-fda928f5-e35f-4888-89ec-e3bbc586be7b"),
(1789625430.719,"assistant-msg-617cd5b3-5755-4069-b17f-ccb6f294cd96"),
(1789625516.968,"assistant-msg-fa9f28e1-ee49-4819-ae04-03d7c8154068"),
(1789625523.781,"assistant-msg-4d3e98bb-09b0-4b12-b207-9bc911c0fcc8"),
(1789625525.212,"assistant-msg-d850b11e-2ac5-45bd-833c-9a7f2f9a352d"),
(1789625526.16,"assistant-msg-da08b42e-6383-45fa-97f2-46bd0836c433"),
(1789625618.517,"assistant-msg-1c18910a-3c0c-45c4-80be-97c152a5ba70"),
(1789625630.969,"assistant-msg-e6c2cfeb-8e71-4395-853d-bd11375f200f"),
(1789625684.703,"assistant-msg-2455557a-65e6-4dfa-a94c-0316ed45d1f3"),
(1789625687.372,"assistant-msg-11fd79a8-3513-4d31-8d64-1a70dc2040e8"),
(1789625693.776,"assistant-msg-ee673f8f-40b5-4488-9b05-462af642df6f"),
(1789625702.72,"assistant-msg-a04d29e8-e541-40d7-af98-98e93c0dc0a7"),
(1789625743.067,"assistant-msg-2a867a3c-f33d-4b8f-be94-df1c8669e219"),
(1789625748.466,"assistant-msg-3a453322-23b6-4a68-8713-6b80caa9a646"),
(1789626290.425,"assistant-msg-962f1a01-53f5-43e7-80f2-cf5d81da9e40"),
(1789626348.326,"assistant-msg-ff621f1b-344a-45b8-93f7-474d97f57bea"),
(1789626356.226,"assistant-msg-a3d981b7-e8dc-4b46-9bb6-1a2536e38c9f"),
(1789626360.076,"assistant-msg-dc0cf5f7-e3e3-478d-a85d-70f49ce11dd6"),
(1789626361.796,"assistant-msg-23e786f6-4ffb-4605-a1dd-90f98075873e"),
(1789626400.879,"assistant-msg-57af8d63-0a50-4716-9679-60adc7c60760"),
(1789626409.307,"assistant-msg-9974ecea-f987-46e2-a497-70cc7926b43b"),
(1789626412.127,"assistant-msg-0eb1cb30-0281-4b22-b60a-9fd35ed44490"),
(1789626493.843,"assistant-msg-73c60d15-c31f-4d7a-a4f1-d5575e6708fc"),
(1789626501.206,"assistant-msg-044b1e63-6838-4838-a249-4285b87146d9"),
(1789626504.883,"assistant-msg-3c6e0464-c6e7-4e98-9044-5d9f23473394"),
(1789626508.388,"assistant-msg-735fc288-90a8-43c5-a925-bc7cf714d7f4"),
(1789626509.198,"assistant-msg-c3930203-cd36-4f63-ac71-9febc0e26991"),
(1789626510.418,"assistant-msg-81bf02b3-bd2f-40ee-917b-a797cb74e08b"),
(1789626527.698,"assistant-msg-e7d1288a-8f50-4b80-9eb8-d36af237233b"),
(1789626583.817,"assistant-msg-1bef42f8-9c25-4f47-945d-ab546f4eda1e"),
(1789626588.548,"assistant-msg-f5ff6b1a-b452-4aa8-ae03-33f71d20fb61"),
(1789626615.434,"assistant-msg-c432db8f-a790-499d-b8e4-8645ede43942"),
(1789626648.053,"assistant-msg-34331e7b-674b-4713-8d89-a6e90ae69793"),
(1789626656.941,"assistant-msg-899aa774-2ce2-4fb6-98e7-bb0cecf52733"),
(1789626660.678,"assistant-msg-d2679f10-5ae4-40d7-be61-292b88ab0827"),
(1789626661.898,"assistant-msg-02d304bd-0ccd-42b8-80db-97135674af9e"),
(1789626663.471,"assistant-msg-3c70e268-9451-4b05-a744-ed2984aa8a6e"),
(1789626664.766,"assistant-msg-59170853-67fc-4cd1-874c-4ebb3f7a1cdb"),
(1789626665.696,"assistant-msg-8fc547f6-7bf7-4509-9256-9905fd02d8ea"),
(1789626667.108,"assistant-msg-0670e9ad-e82f-4a4c-ac01-854c1d350aaf"),
(1789626668.556,"assistant-msg-76e0cc6f-0cce-40cb-9aff-720505fb818f"),
(1789626669.49,"assistant-msg-07ab5fc2-c9a2-4621-bbb1-8b435ef9b4b3"),
(1789626670.752,"assistant-msg-cd4c3f4a-acd8-4608-8005-20e67573f46e"),
(1789626671.746,"assistant-msg-d6cac81f-6c6b-4e6a-9c7e-99b7fbd9c6a1"),
(1789626685.786,"assistant-msg-2f0872e1-89a8-4114-8b6c-0af6a8419864"),
]

# --- spawn hits: (epoch, spawn_id, child, parent) ---
spawn_hits = [
(1789625603,812,"01753ecf-33bc-4ea2-a160-b081c19b6652","802811a3-2226-42dd-b347-9754def28d22"),
(1789625603,813,"57beca27-286f-4044-93a7-80b90039fd29","802811a3-2226-42dd-b347-9754def28d22"),
(1789625607,814,"d5902c84-cf1b-4de4-b9f4-89e3ea184b9b","802811a3-2226-42dd-b347-9754def28d22"),
(1789625606,815,"9bbd7d07-0200-495e-a255-7b19e16a2bea","802811a3-2226-42dd-b347-9754def28d22"),
(1789625606,816,"3148fe34-75cf-4486-9f4a-078e6dd333d7","802811a3-2226-42dd-b347-9754def28d22"),
(1789625606,817,"3a7830e9-c8c0-4aef-ad72-33e7a6cbe9e0","802811a3-2226-42dd-b347-9754def28d22"),
(1789625606,818,"25ee5da7-549b-406b-b918-1c2b7270b646","802811a3-2226-42dd-b347-9754def28d22"),
(1789625606,819,"3064c229-8eaa-4c33-af8d-d213dea7f787","802811a3-2226-42dd-b347-9754def28d22"),
]

seen = set()
if os.path.exists(HITS):
    with open(HITS) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                seen.add((d.get("surface"), str(d.get("ref"))))
            except Exception:
                pass

added = {"chat": 0, "spawn": 0, "daemon": 0}
with open(HITS, "a") as f:
    for e, ref in chat_hits:
        key = ("chat", ref)
        if key in seen:
            continue
        f.write(json.dumps({"ts": iso(e), "surface": "chat",
            "digest": "582bcbd080daeb3f826c45ed4a83b265", "kind": "secondary",
            "length": 96, "ref": ref}) + "\n")
        seen.add(key); added["chat"] += 1
    for e, sid, child, parent in spawn_hits:
        key = ("spawn", str(sid))
        if key in seen:
            continue
        f.write(json.dumps({"ts": iso(e), "surface": "spawn",
            "digest": "b4aefd29108f232f9c0d5a4b030215c1", "kind": "primary",
            "length": 384, "ref": str(sid),
            "child_agent_id": child, "parent_agent_id": parent}) + "\n")
        seen.add(key); added["spawn"] += 1

print(json.dumps({"added": added, "total_new": sum(added.values())}))
