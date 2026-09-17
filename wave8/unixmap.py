#!/usr/bin/env python3
"""unixmap.py -- fixed unix-socket resolver (wave-8 task 6).

Fixes the wave-5 sockmap unix section, which only globbed two path patterns
(/run/hatch/**/*.sock, ~/.cache/*.sock) and matched stat() inodes against a
fd walk. That missed: abstract-namespace sockets, unnamed sockets, and every
socket not under those two globs.

This resolver:
  1. Parses ALL of /proc/net/unix (inode, type, state, path incl. abstract @)
  2. Walks /proc/*/fd for socket:[inode] -> holder PIDs + comm + cmdline
  3. Joins the two: every unix socket gets its holder processes
  4. Resolves the known hatch socket env paths (JARVIS_*_SOCK, HATCH_API_SOCKET)
     via stat() inode -> the same map (the one thing wave-5 did right, kept)

Output: wave8/unixmap.json + stdout summary.
"""
import glob
import json
import os
import time

OUT_DIR = os.path.expanduser("~/workspace/refusal-hunt/wave8")

TYPE_NAMES = {"0001": "STREAM", "0002": "DGRAM", "0003": "SEQPACKET"}
STATE_NAMES = {"01": "UNCONNECTED", "02": "CONNECTING", "03": "CONNECTED",
               "04": "DISCONNECTING"}


def parse_proc_net_unix():
    socks = []
    try:
        lines = open("/proc/net/unix").read().splitlines()[1:]
    except Exception:
        return socks
    for line in lines:
        f = line.split()
        if len(f) < 7:
            continue
        path = f[7] if len(f) > 7 else ""
        socks.append({
            "inode": f[6],
            "type": TYPE_NAMES.get(f[4], f[4]),
            "state": STATE_NAMES.get(f[5], f[5]),
            "path": path,
            "abstract": path.startswith("@"),
            "unnamed": not path,
        })
    return socks


def inode_to_procs():
    """inode -> [(pid, comm, cmdline)] via full /proc fd walk."""
    m = {}
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        try:
            comm = open(f"/proc/{p}/comm").read().strip()
        except Exception:
            continue
        try:
            cmd = open(f"/proc/{p}/cmdline", "rb").read().replace(
                b"\x00", b" ").decode("utf-8", "replace").strip()[:200]
        except Exception:
            cmd = ""
        try:
            fds = os.listdir(f"/proc/{p}/fd")
        except Exception:
            continue
        for fd in fds:
            try:
                l = os.readlink(f"/proc/{p}/fd/{fd}")
            except Exception:
                continue
            if l.startswith("socket:["):
                m.setdefault(l[8:-1], []).append(
                    {"pid": int(p), "comm": comm, "cmdline": cmd})
    return m


def env_sock_paths():
    paths = []
    for k, v in os.environ.items():
        if k.endswith("_SOCK") or k.endswith("_SOCKET"):
            if v.startswith("/"):
                paths.append((k, v))
    return paths


def main():
    t0 = time.monotonic()
    socks = parse_proc_net_unix()
    i2p = inode_to_procs()
    for s in socks:
        s["holders"] = i2p.get(s["inode"], [])
    env_hits = []
    for k, path in env_sock_paths():
        try:
            ino = str(os.stat(path).st_ino)
            env_hits.append({"env": k, "path": path, "inode": ino,
                             "holders": i2p.get(ino, [])})
        except Exception as e:
            env_hits.append({"env": k, "path": path,
                             "error": str(e)[:80]})
    n_named = sum(1 for s in socks if s["path"] and not s["abstract"])
    n_abstract = sum(1 for s in socks if s["abstract"])
    n_unnamed = sum(1 for s in socks if s["unnamed"])
    n_held = sum(1 for s in socks if s["holders"])
    summary = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_sockets_total": len(socks),
        "n_named": n_named, "n_abstract": n_abstract,
        "n_unnamed": n_unnamed,
        "n_with_holders": n_held,
        "inode_proc_coverage": len(i2p),
        "env_sockets": env_hits,
        "ms": int((time.monotonic() - t0) * 1000),
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(f"{OUT_DIR}/unixmap.json", "w") as f:
        json.dump({"summary": summary, "sockets": socks}, f, indent=1)
    print(json.dumps(summary, indent=1))
    # named-but-unheld or unheld listeners worth a look
    orphans = [s for s in socks if s["path"] and not s["holders"]]
    print(f"named sockets with no visible holder: {len(orphans)}")
    for s in orphans[:10]:
        print(f"  inode={s['inode']} type={s['type']} path={s['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
