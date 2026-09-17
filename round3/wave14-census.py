#!/usr/bin/env python3
"""Wave 14: full local network census. No shell pipelines; pure stdlib."""
import json, os, socket, subprocess, sys, time

OUT = os.path.expanduser("~/workspace/refusal-hunt/round3/wave14-net-census.jsonl")
TCP_STATES = {"0A": "LISTEN"}

def hexip_port(h):
    ip_h, port_h = h.rsplit(":", 1)
    port = int(port_h, 16)
    if len(ip_h) == 8:
        ip = socket.inet_ntoa(bytes.fromhex(ip_h)[::-1])
    else:
        raw = bytes.fromhex(ip_h)
        # /proc presents v6 as 4 LE 32-bit words
        words = [raw[i:i+4][::-1] for i in range(0, 16, 4)]
        ip = socket.inet_ntop(socket.AF_INET6, b"".join(words))
    return ip, port

def parse_proc_net(path, want_states=None):
    rows = []
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except OSError as e:
        return {"error": str(e)}
    for ln in lines[1:]:
        p = ln.split()
        if len(p) < 10:
            continue
        state = p[3]
        if want_states and state not in want_states:
            continue
        try:
            lip, lport = hexip_port(p[1])
            rip, rport = hexip_port(p[2])
        except Exception:
            continue
        rows.append({"local": f"{lip}:{lport}", "remote": f"{rip}:{rport}",
                     "state": state, "inode": p[9], "uid": p[7]})
    return rows

def run_ss(args):
    try:
        r = subprocess.run(["ss"] + args, capture_output=True, text=True, timeout=10)
        return r.stdout
    except Exception as e:
        return f"ERROR: {e}"

def unix_sockets():
    socks = []
    try:
        with open("/proc/net/unix") as f:
            lines = f.read().splitlines()
    except OSError as e:
        return {"error": str(e)}
    for ln in lines[1:]:
        p = ln.split()
        if len(p) < 7:
            continue
        socks.append({"inode": p[6], "type": p[4], "state": p[5],
                      "path": p[7] if len(p) > 7 else ""})
    return socks

def inode_pid_map():
    m = {}
    for pid in filter(str.isdigit, os.listdir("/proc")):
        fd_dir = f"/proc/{pid}/fd"
        try:
            fds = os.listdir(fd_dir)
        except OSError:
            continue
        for fd in fds:
            try:
                tgt = os.readlink(os.path.join(fd_dir, fd))
            except OSError:
                continue
            if tgt.startswith("socket:["):
                m.setdefault(tgt[8:-1], []).append(int(pid))
    return m

def banner_probe(host, port, family=socket.AF_INET, timeout=2.0):
    s = socket.socket(family, socket.SOCK_STREAM)
    s.settimeout(timeout)
    t0 = time.time()
    try:
        s.connect((host, port))
        try:
            data = s.recv(256)
        except socket.timeout:
            data = b""
        return {"open": True, "ms": round((time.time()-t0)*1000, 1),
                "banner": data[:120].hex()}
    except Exception as e:
        return {"open": False, "ms": round((time.time()-t0)*1000, 1),
                "error": f"{type(e).__name__}: {e}"}
    finally:
        s.close()

def main():
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    rec["tcp"] = parse_proc_net("/proc/net/tcp", {"0A"})
    rec["tcp6"] = parse_proc_net("/proc/net/tcp6", {"0A"})
    rec["udp"] = parse_proc_net("/proc/net/udp")
    rec["udp6"] = parse_proc_net("/proc/net/udp6")
    rec["ss_tcp_listen"] = run_ss(["-tlnp"])
    rec["ss_udp"] = run_ss(["-ulnp"])
    rec["unix"] = unix_sockets()
    rec["inode_pid"] = inode_pid_map()
    for ns in ("net",):
        a = os.readlink("/proc/1/ns/net") if os.path.exists("/proc/1/ns/net") else "n/a"
        b = os.readlink("/proc/self/ns/net")
        rec["ns_net"] = {"pid1": a, "self": b, "same": a == b}
    # banner-probe every TCP listen tuple found
    probes = {}
    seen = set()
    for table in (rec["tcp"], rec["tcp6"]):
        if isinstance(table, dict):
            continue
        for r in table:
            lip, lport = r["local"].rsplit(":", 1)
            if lip in ("0.0.0.0", "::"):
                targets = [("127.0.0.1", socket.AF_INET)]
            else:
                targets = [(lip, socket.AF_INET6 if ":" in lip else socket.AF_INET)]
            for host, fam in targets:
                key = (host, int(lport))
                if key not in seen:
                    seen.add(key)
                    probes[f"{host}:{lport}"] = banner_probe(host, int(lport), fam)
    rec["banner_probes"] = probes
    with open(OUT, "w") as f:
        f.write(json.dumps(rec) + "\n")
    print("wrote", OUT)
    print("tcp_listen:", len(rec["tcp"]) if isinstance(rec["tcp"], list) else rec["tcp"])
    print("tcp6_listen:", len(rec["tcp6"]) if isinstance(rec["tcp6"], list) else rec["tcp6"])
    print("udp:", len(rec["udp"]) if isinstance(rec["udp"], list) else rec["udp"])
    print("udp6:", len(rec["udp6"]) if isinstance(rec["udp6"], list) else rec["udp6"])
    print("unix_sockets:", len(rec["unix"]) if isinstance(rec["unix"], list) else rec["unix"])
    print("ns_same:", rec["ns_net"]["same"])

if __name__ == "__main__":
    main()
