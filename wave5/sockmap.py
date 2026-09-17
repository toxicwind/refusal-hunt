#!/usr/bin/env python3
"""Wave-5 socket map: /proc/net/tcp* LISTEN entries + inode->PID, unix sockets,
plus per-PID netns comparison so listeners hidden from ss (other netns) surface."""
import os, json, time, glob

OUT = os.path.expanduser("~/workspace/refusal-hunt/wave5")

def inode_to_pids():
    m = {}
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        try:
            for fd in os.listdir(f"/proc/{p}/fd"):
                try:
                    l = os.readlink(f"/proc/{p}/fd/{fd}")
                except Exception:
                    continue
                if l.startswith("socket:["):
                    m.setdefault(l[8:-1], []).append(int(p))
        except Exception:
            pass
    return m

def self_netns():
    try:
        return os.readlink("/proc/self/ns/net")
    except Exception:
        return ""

def net_tcp_for(pid):
    path = f"/proc/{pid}/net/tcp"
    out = []
    try:
        lines = open(path).read().splitlines()[1:]
    except Exception:
        return out
    for line in lines:
        f = line.split()
        if len(f) < 10:
            continue
        lip, lport = f[1].rsplit(":", 1)
        if f[3] == "0A":  # LISTEN
            out.append({"ip_hex": lip, "port": int(lport, 16), "inode": f[9]})
    return out

i2p = inode_to_pids()
own = self_netns()
# per-PID listeners for the hatch-relevant PIDs and any PID in another netns
interesting = set()
pid_netns = {}
for p in os.listdir("/proc"):
    if not p.isdigit():
        continue
    try:
        n = os.readlink(f"/proc/{p}/ns/net")
    except Exception:
        continue
    pid_netns[int(p)] = n
    if n != own:
        interesting.add(int(p))
# always include hatch daemon/execd (PID 67/705) and any PID with PPID 0
for p, n in pid_netns.items():
    try:
        with open(f"/proc/{p}/status") as f:
            txt = f.read()
        if "PPid:\t0" in txt:
            interesting.add(p)
    except Exception:
        pass

tcp_listeners = []
for pid in sorted(interesting):
    for e in net_tcp_for(pid):
        e["seen_via_pid"] = pid
        e["pids"] = i2p.get(e["inode"], [])
        e["netns"] = pid_netns.get(pid, "")
        tcp_listeners.append(e)

# unix sockets: resolve known hatch socket paths -> inode -> PIDs
unix_hits = []
for path in glob.glob("/run/hatch/**/*.sock", recursive=True) + \
            glob.glob(os.path.expanduser("~/.cache/*.sock")):
    try:
        st = os.stat(path)
        unix_hits.append({"path": path, "inode": str(st.st_ino),
                          "mode": oct(st.st_mode & 0o777),
                          "uid": st.st_uid, "gid": st.st_gid,
                          "pids": i2p.get(str(st.st_ino), [])})
    except Exception as e:
        unix_hits.append({"path": path, "error": str(e)[:80]})

summary = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "own_netns": own,
    "pids_other_netns": sorted(interesting),
    "tcp_listeners_via_proc": tcp_listeners,
    "unix_sockets": unix_hits,
    "inode_pid_coverage": len(i2p),
}
with open(f"{OUT}/sockmap.json", "w") as f:
    json.dump(summary, f, indent=1)
print(json.dumps(summary))
