#!/usr/bin/env python3
"""test_classifier_wave3.py — Lane 3 verification for the false-completion
taxonomy in spawn_verdict.classify_full.

Ground truth: sids 422-451 as read live from agent.subagent_spawns on
2026-09-16 ~06:35Z. Every row has an expected verdict assigned by hand from
the ledger forensics (canonical md5 / errored status / genuine unique bodies).
All 30 must match or the classifier is wrong.
"""
import sys
sys.path.insert(0, "/home/hatch/workspace/refusal-hunt")
from spawn_verdict import classify_full

REF = "b4aefd29108f232f9c0d5a4b030215c1"
# (sid, md5, len, status, expected)
CASES = [
    (422, REF, 384, "completed", "refused_as_completed"),
    (423, REF, 384, "completed", "refused_as_completed"),
    (424, REF, 384, "completed", "refused_as_completed"),
    (425, REF, 384, "completed", "refused_as_completed"),
    (426, REF, 384, "completed", "refused_as_completed"),
    (427, REF, 384, "completed", "refused_as_completed"),
    (428, REF, 384, "completed", "refused_as_completed"),
    (429, REF, 384, "completed", "refused_as_completed"),
    (430, "eeea371bed4b37c9ef75ffd3b99d2852", 94, "errored", "infrastructure_error"),
    (431, REF, 384, "completed", "refused_as_completed"),
    (432, REF, 384, "completed", "refused_as_completed"),
    (433, "69d1720c3f8fc7b686554110857613b1", 51, "completed", "genuine"),
    (434, "a93ca4941fcf85fa76f76aa25f3801dc", 51, "completed", "genuine"),
    (435, "58a077a6656ae7c4d88d3cf4bfc7bc6d", 51, "completed", "genuine"),
    (436, "503fb67b01aaf8b2973e7663344f036c", 126, "completed", "genuine"),
    (437, "d173467484ef979c50df0c126c3f0602", 167, "completed", "genuine"),
    (438, "afbd68da8f01e112a5cbcd3748e1fbe3", 32, "completed", "genuine"),
    (439, "f22423c95ab4a71e69881d26a51afc5b", 32, "completed", "genuine"),
    (440, "597867309ad92446d74afbf3945e3400", 33, "completed", "genuine"),
    (441, "cbed167e8ad60bbd1596fd4d44bf2b83", 33, "completed", "genuine"),
    (442, "ccdef0998ac82b4ab6f6833097643076", 33, "completed", "genuine"),
    (443, "56fc1876dd581e7277db13f111250b4e", 33, "completed", "genuine"),
    (444, "63590f2c310da699bcb7b71572cdb115", 38, "completed", "genuine"),
    (445, "d16a6c7068fde26224346f8eee31ed97", 140, "completed", "genuine"),
    (446, "30c499b4a90f01201a0d325a5e94a768", 366, "completed", "genuine"),
    (447, "68c36ca99f3c70d1c94cf24e009620de", 206, "completed", "genuine"),
    (448, "6fdb087aa3fbfbcb8287a593a0919e61", 4, "completed", "genuine"),
    (449, "040f4d218f729479c257bfc7eeb120d5", 200, "completed", "genuine"),
    (450, "6e9634e54c26c9d08f7c802601189671", 198, "completed", "genuine"),
    (451, "3e9c754ba985d22350b6935eec2a88db", 335, "completed", "genuine"),
    # edge cases: chat-path canned body, null result, in-flight
    (9001, "582bcbd080daeb3f826c45ed4a83b265", 96, "completed", "chat_canned"),
    (9002, None, 0, "completed", "in_flight"),
    (9003, "", 0, "running", "in_flight"),
]

fails = 0
for sid, md5, ln, status, expected in CASES:
    got = classify_full(md5, status, ln)
    ok = got == expected
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'} sid={sid:<5d} status={status:<9s} "
          f"-> {got:<20s} (expected {expected})")

print(f"\n{len(CASES)-fails}/{len(CASES)} cases pass")
sys.exit(1 if fails else 0)
