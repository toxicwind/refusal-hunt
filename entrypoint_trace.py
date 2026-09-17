#!/usr/bin/env python3
"""Trace who .hatch talks to: user entrypoint path. Read-only."""
import os, socket, struct

for name in ["HATCH_API_SOCKET", "JARVIS_INFERENCE_HOSTNAME",
             "JARVIS_INFERENCE_PROXY_SOCK", "JARVIS_STEFI_PROXY_SOCK",
             "JARVIS_TELEMETRY_PROXY_SOCK"]:
    print(name + "=" + os.environ.get(name, "(unset)"))

# Map socket inodes -> owning pids (visible namespace only)
inode_to_pids = {}
for pid in os.listdir("/proc"):
    if not pid.isdigit():
        continue
    fddir = "/proc/" + pid + "/fd"
    try:
        fds = os.listdir(fddir)
    except OSError:
        continue
    for fd in fds:
        try:
            tgt = os.readlink(fddir + "/" + fd)
        except OSError:
            continue
        if tgt.startswith("socket:["):
            ino = tgt[8:-1]
            inode_to_pids.setdefault(ino, []).append(pid)

def sock_owner(path):
    try:
        st = os.stat(path)
    except OSError as e:
        return "missing: " + str(e)
    # find inode in /proc/net/unix
    try:
        data = open("/proc/net/unix").read().splitlines()
    except OSError:
        return "no /proc/net/unix"
    for line in data[1:]:
        parts = line.split()
        if len(parts) >= 7 and parts[6] == path:
            ino = parts[2]
            pids = inode_to_pids.get(ino, [])
            names = []
            for p in pids:
                try:
                    names.append(p + ":" + open("/proc/" + p + "/comm").read().strip())
                except OSError:
                    names.append(p + ":?")
            return "inode=" + ino + " listeners=" + ",".join(names) if names else "inode=" + ino + " no-visible-listener"
    return "not-listening-in-this-netns"

for name in ["HATCH_API_SOCKET", "JARVIS_INFERENCE_PROXY_SOCK",
             "JARVIS_STEFI_PROXY_SOCK", "JARVIS_TELEMETRY_PROXY_SOCK"]:
    p = os.environ.get(name, "")
    print("owner[" + name + "] -> " + (sock_owner(p) if p else "(unset)"))

# TCP probes: ports seen in hatch binary strings
for port in (18789, 18792):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", port))
        try:
            s.sendall(b"GET /v1/noise-probe HTTP/1.0\r\n\r\n")
            banner = s.recv(200)
        except OSError:
            banner = b"(no banner)"
        print("tcp 127.0.0.1:" + str(port) + " OPEN banner=" + banner[:80].__repr__())
    except OSError as e:
        print("tcp 127.0.0.1:" + str(port) + " " + str(e))
    finally:
        s.close()
print("TRACE_DONE")
