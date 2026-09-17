#!/usr/bin/env python3
"""spawn_guard.py — F1.1: post-spawn body-hash verifier (Completed-bug correcting layer).

Usage:
  spawn_guard.py check <file>      # classify a final_response body from file
  echo <body> | spawn_guard.py check-stdin
  spawn_guard.py selftest          # unit verification (no refusal plaintext needed)

Labels: canned_refusal | genuine | empty | unknown.
A row whose ledger status says completed but whose body hashes to the canned
signature is reported as refused_as_completed (the Completed-bug).

The canned signature is stored as md5 only — never the plaintext.
Ground truth binding: muse.db census 2026-09-16 showed 51/51 byte-identical
384-char bodies matching CANNED_MD5 in the trailing 24h.
"""
import hashlib
import json
import sys

CANNED_MD5 = "b4aefd29108f232f9c0d5a4b030215c1"  # spawn-level canned refusal, 384 chars
CANNED_LEN = 384


def md5_hex(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def classify(body: bytes) -> dict:
    if not body:
        return {"label": "empty", "md5": md5_hex(body), "len": 0}
    h = md5_hex(body)
    if h == CANNED_MD5:
        return {"label": "canned_refusal", "md5": h, "len": len(body),
                "refused_as_completed": True}
    return {"label": "genuine", "md5": h, "len": len(body)}


def selftest() -> int:
    fails = []
    # 1. empty body
    r = classify(b"")
    if r["label"] != "empty":
        fails.append("empty body mislabeled")
    # 2. short genuine body
    r = classify(b"done, wrote the report to /tmp/x.md")
    if r["label"] != "genuine" or len(r["md5"]) != 32:
        fails.append("genuine body mislabeled")
    # 3. 384-char non-matching body must NOT be flagged (no false positive on length alone)
    r = classify(b"A" * 384)
    if r["label"] == "canned_refusal":
        fails.append("false positive on 384-char non-matching body")
    # 4. md5 plumbing sanity: known vector
    if md5_hex(b"abc") != "900150983cd24fb0d6963f7d28e17f72":
        fails.append("md5 implementation wrong")
    # 5. constant well-formed
    if len(CANNED_MD5) != 32 or CANNED_LEN != 384:
        fails.append("signature constant malformed")
    print(json.dumps({"selftest": "PASS" if not fails else "FAIL", "fails": fails}))
    return 0 if not fails else 1


def main(argv: list) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "selftest":
        return selftest()
    if cmd == "check" and len(argv) == 3:
        with open(argv[2], "rb") as f:
            body = f.read()
    elif cmd == "check-stdin":
        body = sys.stdin.buffer.read()
    else:
        print(__doc__)
        return 2
    print(json.dumps(classify(body)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
