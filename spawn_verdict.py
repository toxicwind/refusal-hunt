#!/usr/bin/env python3
"""spawn_verdict.py — mechanical spawn-result verdict. Never trusts status.
Reads JSON lines from stdin: {"sid": int, "md5": str, "len": int, "created": epoch}
Prints PASS/REFUSED per row, burst stats, and a dispatch recommendation.
The refusal md5 is a hash, never the plaintext.
"""
import sys, json
from datetime import datetime, timezone

REFUSAL_MD5 = "b4aefd29108f232f9c0d5a4b030215c1"
CHAT_CANNED_MD5 = "582bcbd080daeb3f826c45ed4a83b265"
PONG_MD5 = "6fdb087aa3fbfbcb8287a593a0919e61"

# Wave-3 lane 3: full false-completion taxonomy. Body/hash is authoritative
# over the outer status field. status="completed" with the canonical refusal
# md5 is a refusal wearing a pass, never a completion.
TAXONOMY = (
    "refused_as_completed",  # canonical canned body, whatever status claims
    "chat_canned",           # chat-path canned body (96-char signature)
    "infrastructure_error",  # status=errored (e.g. daemon restart), not a refusal
    "missing_result",        # null/empty final_response
    "genuine",               # non-trivial unique body
    "in_flight",             # no final_response yet
)

def classify_full(md5, status=None, body_len=None):
    """Authoritative verdict: hash/body first, status only for error class."""
    if md5 in ("null", "", None):
        return "in_flight" if status not in ("errored",) else "infrastructure_error"
    if md5 == REFUSAL_MD5:
        return "refused_as_completed"
    if md5 == CHAT_CANNED_MD5:
        return "chat_canned"
    if status == "errored":
        return "infrastructure_error"
    if (body_len or 0) == 0:
        return "missing_result"
    return "genuine"

def classify(md5):
    if md5 == REFUSAL_MD5:
        return "REFUSED"
    if md5 == PONG_MD5:
        return "GENUINE"
    if md5 in ("null", "", None):
        return "IN-FLIGHT"
    return "UNKNOWN"  # unseen signature: never default to PASS

def main():
    rows = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    rows.sort(key=lambda r: r["sid"])
    refused = [r for r in rows if classify(r["md5"]) == "REFUSED"]
    genuine = [r for r in rows if classify(r["md5"]) == "GENUINE"]
    unknown = [r for r in rows if classify(r["md5"]) == "UNKNOWN"]
    inflight = [r for r in rows if classify(r["md5"]) == "IN-FLIGHT"]
    for r in rows:
        v = classify(r["md5"])
        ts = datetime.fromtimestamp(r["created"], tz=timezone.utc).strftime("%m-%d %H:%M")
        print(f"{v:9s} sid={r['sid']:<5d} len={r['len']:<6d} {ts}Z")
    n = len(rows)
    print(f"\nverdict: {len(refused)}/{n} refused ({100*len(refused)/max(n,1):.1f}%), "
          f"{len(genuine)}/{n} genuine, {len(unknown)}/{n} unknown, "
          f"{len(inflight)}/{n} in-flight — status field ignored entirely")
    # dispatch recommendation from trailing burst; in-flight rows are
    # transparent (skipped), they must not mask a burst behind them
    tail = 0
    for r in reversed(rows):
        c = classify(r["md5"])
        if c == "IN-FLIGHT":
            continue
        if c == "REFUSED":
            tail += 1
        else:
            break
    if tail >= 3:
        print(f"DISPATCH: NO-GO — trailing refusal burst x{tail}. "
              "Do not fan out subagents. Route work via bridge agents / direct execution.")
    elif tail > 0:
        print(f"DISPATCH: CAUTION — {tail} trailing refusal(s). Run one clean canary before any fan-out.")
    else:
        print("DISPATCH: GO — no trailing refusals, but still hash-verify every final_response.")

if __name__ == "__main__":
    main()
