#!/usr/bin/env python3
"""tool_audit_hook.py -- the ONE consistent way to launch shell commands.

Every shell command goes through this hook. It:
  1. Runs the command under `sudo unshare -rm` (root, fresh mount+net ns).
  2. Times it with a monotonic clock (per-attempt latency is first-class).
  3. Captures exit code, byte counts, sha256 of stdout/stderr.
  4. Appends a JSONL audit row to tool-audit.jsonl (tracks the internal
     exec tool's behavior over time: aborts, empty outputs, slow runs).
  5. Flags anomaly shapes: ABORTED, EMPTY_NONZERO, SLOW (>3s ceiling),
     TRUNCATED.

Usage: tool_audit_hook.py '<shell command string>'
The command's own stdout/stderr are replayed verbatim; the audit row goes
only to the JSONL file (plus a one-line HOOK_AUDIT summary on stderr).
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

AUDIT = "/home/hatch/workspace/refusal-hunt/tool-audit.jsonl"
SLOW_MS = 3000


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: tool_audit_hook.py '<command>'", file=sys.stderr)
        return 2
    cmd = sys.argv[1]
    t0 = time.monotonic()
    wall = datetime.now(timezone.utc).isoformat()
    # Single-wrap contract: the hook is the ONLY unshare boundary. Never call
    # the hook from inside another `sudo unshare -rm` (nested sudo cannot
    # re-escalate inside a user namespace and fails EMPTY_NONZERO). If we are
    # already namespaced root, run direct and flag it.
    already_ns = False
    argv = ["sudo", "unshare", "-rm", "bash", "-c", cmd]
    try:
        if os.geteuid() == 0:
            argv = ["bash", "-c", cmd]
            already_ns = True
    except OSError:
        pass
    try:
        p = subprocess.run(argv, capture_output=True, timeout=120)
        out, err, code = p.stdout, p.stderr, p.returncode
        timeout = False
    except subprocess.TimeoutExpired as e:
        out, err, code, timeout = e.stdout or b"", e.stderr or b"", 124, True

    dur_ms = int((time.monotonic() - t0) * 1000)
    flags = []
    if already_ns:
        flags.append("ALREADY_NS")
    if timeout:
        flags.append("TIMEOUT")
    if code != 0 and len(out.strip()) == 0:
        flags.append("EMPTY_NONZERO")
    if dur_ms > SLOW_MS:
        flags.append("SLOW")
    blob = out + err
    if b"aborted" in blob.lower() and len(blob) < 200:
        flags.append("ABORTED")

    row = {
        "ts": wall,
        "cmd_preview": cmd[:160],
        "cmd_sha": sha(cmd.encode()),
        "duration_ms": dur_ms,
        "exit": code,
        "stdout_len": len(out),
        "stderr_len": len(err),
        "stdout_sha": sha(out),
        "stderr_sha": sha(err),
        "flags": flags,
    }
    with open(AUDIT, "a") as f:
        f.write(json.dumps(row) + "\n")

    sys.stdout.buffer.write(out)
    sys.stderr.buffer.write(err)
    sys.stderr.write(
        f"HOOK_AUDIT exit={code} {dur_ms}ms out={len(out)}B err={len(err)}B "
        f"flags={','.join(flags) or 'ok'}\n"
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
