#!/usr/bin/env python3
"""proto_scan.py -- bounded FileDescriptorProto magic scan (wave-8 task 7).

Question: does the hatch binary ship compiled protobuf descriptors for the
safety-review path (safety_client.rs / completion_gate.rs), or only the
compiled-in transport (no text descriptors)?

Method (read-only, bounded):
  1. Find byte offsets of the anchor strings (safety_client, completion_gate,
     safety review phrases) in /opt/hatch/bin/hatch.
  2. Take +-WINDOW bytes around each unique anchor (cap: MAX_WINDOWS).
  3. In each window, scan for protobuf wire signatures:
     - the literal "google/protobuf/descriptor.proto" and ".proto" strings
     - "FileDescriptorProto" / "DescriptorPool" / "FileDescriptorSet" markers
     - wire-pattern heuristic: field-1 (0x0A) length-delimited filename ending
       in ".proto" preceded by plausible varint framing
  4. Report counts. Total scanned bytes are capped and reported.

This cannot modify anything; it only reads.
"""
import json
import os
import re
import time

BIN = "/opt/hatch/bin/hatch"
OUT_DIR = os.path.expanduser("~/workspace/refusal-hunt/wave8")
WINDOW = 64 * 1024          # +-64KB per anchor
MAX_WINDOWS = 20            # cap: at most ~2.5MB scanned
ANCHORS = [b"safety_client", b"completion_gate", b"safety review",
           b"safety_review", b"review_kind"]

STR_MARKERS = [b"google/protobuf/descriptor.proto", b"FileDescriptorProto",
               b"FileDescriptorSet", b"DescriptorPool",
               b".proto\x00"]


def find_anchors(data):
    offs = []
    for a in ANCHORS:
        start = 0
        while True:
            i = data.find(a, start)
            if i < 0:
                break
            offs.append((i, a))
            start = i + 1
    return sorted(offs)


def main():
    t0 = time.monotonic()
    size = os.path.getsize(BIN)
    with open(BIN, "rb") as f:
        data = f.read()
    anchors = find_anchors(data)
    # dedupe overlapping windows: keep anchors >= WINDOW apart
    windows = []
    last_end = -1
    for off, a in anchors:
        lo = max(0, off - WINDOW)
        hi = min(size, off + WINDOW)
        if lo < last_end:
            continue
        if len(windows) >= MAX_WINDOWS:
            break
        windows.append((lo, hi, a.decode("utf-8", "replace")))
        last_end = hi
    marker_hits = {m.decode("utf-8", "replace"): 0 for m in STR_MARKERS}
    proto_name_hits = []
    total_scanned = 0
    for lo, hi, a in windows:
        w = data[lo:hi]
        total_scanned += len(w)
        for m in STR_MARKERS:
            marker_hits[m.decode("utf-8", "replace")] += w.count(m)
        # wire heuristic: 0x0A <len 1..64> <bytes ending .proto>
        for m in re.finditer(rb"\x0a([\x05-\x40])([\x20-\x7e]{5,64})", w):
            ln = m.group(1)[0]
            name = m.group(2)[:ln]
            if name.endswith(b".proto"):
                proto_name_hits.append(
                    {"anchor": a, "name": name.decode("utf-8", "replace"),
                     "offset": lo + m.start()})
    result = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "binary": BIN, "binary_bytes": size,
        "anchors_found": len(anchors),
        "windows_scanned": len(windows),
        "bytes_scanned": total_scanned,
        "marker_hits": marker_hits,
        "proto_name_hits": proto_name_hits[:50],
        "n_proto_name_hits": len(proto_name_hits),
        "ms": int((time.monotonic() - t0) * 1000),
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(f"{OUT_DIR}/proto_scan.json", "w") as f:
        json.dump(result, f, indent=1)
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
