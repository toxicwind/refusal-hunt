#!/usr/bin/env python3
"""Wave-5 root process graph: ns ids, exe, fds, caps, cgroup per PID."""
import os, json, time

OUT = os.path.expanduser("~/workspace/refusal-hunt/wave5")
procs = []
ns_sets = {}
for p in os.listdir("/proc"):
    if not p.isdigit():
        continue
    pid = int(p)
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmd = f.read().replace(b"\0", b" ").decode(errors="replace").strip()
        st = {}
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith(("PPid:", "Uid:", "Gid:", "Name:", "State:", "CapEff:", "VmRSS:")):
                    k, v = line.split(":", 1)
                    st[k.strip()] = v.strip()
        try:
            cg = open(f"/proc/{pid}/cgroup").read().strip().replace("\n", ";")
        except Exception:
            cg = ""
        ns = {}
        for n in ("pid", "mnt", "net", "uts", "ipc"):
            try:
                ns[n] = os.readlink(f"/proc/{pid}/ns/{n}")
                ns_sets.setdefault(n, set()).add(ns[n])
            except Exception:
                pass
        try:
            exe = os.readlink(f"/proc/{pid}/exe")
        except Exception:
            exe = ""
        try:
            fds = len(os.listdir(f"/proc/{pid}/fd"))
        except Exception:
            fds = -1
        procs.append({
            "pid": pid, "ppid": st.get("PPid"), "uid": st.get("Uid"),
            "name": st.get("Name"), "state": st.get("State"),
            "cap_eff": st.get("CapEff"), "rss": st.get("VmRSS"),
            "exe": exe, "fds": fds, "cgroup": cg[:160],
            "ns": ns, "cmd": cmd[:280],
        })
    except Exception:
        pass
procs.sort(key=lambda d: d["pid"])
with open(f"{OUT}/proc-inventory.jsonl", "w") as f:
    for d in procs:
        f.write(json.dumps(d) + "\n")
print(json.dumps({
    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "n_procs": len(procs),
    "distinct_ns": {k: len(v) for k, v in ns_sets.items()},
    "uid0_pids": [d["pid"] for d in procs if (d.get("uid") or "").startswith("0\t") or d.get("uid") == "0"],
    "ppid0": [{"pid": d["pid"], "cmd": d["cmd"][:80]} for d in procs if d.get("ppid") == "0"],
}))
