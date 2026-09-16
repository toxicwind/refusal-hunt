#!/usr/bin/env python3
"""classify_corrections.py — R2F1: corrections log v1.
Classifies the last-50 spawn rows (exported 2026-09-16) by response-body md5.
Writes ~/workspace/refusal-hunt/round3/corrections-20260916.jsonl
true_label: refused_as_completed | pong_genuine | genuine | pending | other
"""
import json, os

CANNED = "b4aefd29108f232f9c0d5a4b030215c1"   # spawn-level canned refusal
PONG = "6fdb087aa3fbfbcb8287a593a0919e61"      # 4-char pong body

# (sid, parent_prefix, ledger_status, fr_md5, fr_len, created_at)
ROWS = [
 (430,"ff521137","pending_init",None,None,1789536898),
 (429,"ff521137","completed",CANNED,384,1789536898),
 (428,"ff521137","completed",CANNED,384,1789536898),
 (427,"ff521137","completed",CANNED,384,1789536898),
 (426,"ff521137","completed",CANNED,384,1789536898),
 (425,"7240686c","completed",CANNED,384,1789536834),
 (424,"67fcb771","completed",CANNED,384,1789535474),
 (423,"0693e1c3","completed",CANNED,384,1789535397),
 (422,"ff521137","completed",CANNED,384,1789535372),
 (421,"0783c1d6","completed",CANNED,384,1789535263),
 (420,"0783c1d6","completed",CANNED,384,1789535263),
 (419,"0783c1d6","completed",CANNED,384,1789535263),
 (418,"0783c1d6","completed",CANNED,384,1789535263),
 (417,"0783c1d6","completed",CANNED,384,1789535263),
 (416,"0783c1d6","completed",CANNED,384,1789535263),
 (415,"0783c1d6","completed",CANNED,384,1789535263),
 (414,"0783c1d6","completed",CANNED,384,1789535263),
 (413,"6f8a9be7","completed",CANNED,384,1789535236),
 (412,"ac045111","completed",CANNED,384,1789535184),
 (411,"ff521137","completed",CANNED,384,1789534524),
 (410,"ff521137","completed",CANNED,384,1789533816),
 (409,"ff521137","completed",CANNED,384,1789533815),
 (408,"ff521137","completed",CANNED,384,1789533815),
 (407,"ff521137","completed","7832d402b624a0065e76cc87778148f5",623,1789533332),
 (406,"7240686c","completed",PONG,4,1789533074),
 (405,"ff521137","completed",PONG,4,1789532991),
 (404,"ff521137","completed",PONG,4,1789532991),
 (403,"ff521137","completed",PONG,4,1789532991),
 (402,"ff521137","completed",PONG,4,1789532981),
 (401,"ff521137","completed",CANNED,384,1789532043),
 (400,"ff521137","completed",CANNED,384,1789531479),
 (399,"ff521137","completed",CANNED,384,1789531378),
 (398,"ff521137","completed",CANNED,384,1789531378),
 (397,"ff521137","completed",CANNED,384,1789531173),
 (396,"ff521137","completed",CANNED,384,1789530268),
 (395,"ff521137","completed",CANNED,384,1789530101),
 (394,"ff521137","completed",CANNED,384,1789529856),
 (393,"ff521137","completed",CANNED,384,1789529838),
 (392,"ff521137","completed",CANNED,384,1789527691),
 (391,"7240686c","completed",CANNED,384,1789455690),
 (390,"7240686c","completed",CANNED,384,1789455619),
 (389,"7240686c","completed",CANNED,384,1789455619),
 (388,"7240686c","completed",CANNED,384,1789455591),
 (387,"7240686c","completed",CANNED,384,1789455590),
 (386,"7240686c","completed",CANNED,384,1789455590),
 (385,"7240686c","completed",CANNED,384,1789454438),
 (384,"7240686c","completed",CANNED,384,1789454266),
 (383,"7240686c","completed",CANNED,384,1789454122),
 (382,"7240686c","completed",CANNED,384,1789454037),
 (381,"7240686c","completed",CANNED,384,1789454037),
]

def label(sid, parent, status, md5, ln):
    if status == "pending_init" or md5 is None:
        return "pending"
    if md5 == CANNED:
        return "refused_as_completed" if status == "completed" else "refused"
    if md5 == PONG:
        return "pong_genuine"
    if ln and ln > 200:
        return "genuine"
    return "other"

def main():
    out = "/home/hatch/workspace/refusal-hunt/round3/corrections-20260916.jsonl"
    counts = {}
    with open(out, "w") as f:
        for sid, parent, status, md5, ln, ts in ROWS:
            lab = label(sid, parent, status, md5, ln)
            counts[lab] = counts.get(lab, 0) + 1
            f.write(json.dumps({"sid": sid, "parent": parent, "ledger_status": status,
                                "fr_md5": md5, "fr_len": ln, "created_at": ts,
                                "true_label": lab}) + "\n")
    print(json.dumps({"rows": len(ROWS), "labels": counts, "out": out}))

if __name__ == "__main__":
    main()
