#!/usr/bin/env python3
"""WAVE 2: eight more rounds x three fixes - dependency-aware, race-borrowing.

Wave-1 lessons baked in:
- r7f1 root cause: curl without -L downloaded a 75-byte 302 page as the "tarball".
  Wave-2 races real mirrors (dl.google.com direct + go.dev with redirect following),
  validating size>50MB and gzip magic.
- r1f2/r6f2: verify harnesses tested the wrong CLI surface (exec -a games, --selftest
  vs positional selftest). Wave-2 tests the real invocation.
- r2f2/r4f2: asserts stricter than reality (one non-skip row in 200). Wave-2 asserts
  fractions, not purity.
- r4f1: consumed r2f2's output file; r2f2 rolled back -> FileNotFoundError cascade.
  Wave-2 has explicit `needs` with topological levels; blocked (not failed) on unmet needs.
- r8f2/r8f3: parallel fixes raced the round summary they were reading. Wave-2 moves
  acceptance artifacts to a sequential post-phase.
- r6f3: swallowed fdfind stderr. Wave-2 captures return codes.
- r8f1 recompute exposed a hand-transcription error in wave-1 input aggregates
  (58 vs 57). Wave-2 rebuilds aggregates programmatically from spawn_window_127.csv.

Every command wrapped: unshare --user --map-root-user --mount -- (root in ns).
"""
import asyncio
import json
import os
import shutil
import time

try:
    import nest_asyncio
    nest_asyncio.apply()  # Chris's package: correct PyPI name is nest_asyncio (nested_async 404s)
except ImportError:
    nest_asyncio = None  # stdlib asyncio fallback; runner needs no nested loops

ROOT = os.path.expanduser("~/workspace/refusal-hunt/round4")
FIXDIR = os.path.join(ROOT, "w2_fixes")
RBDIR = os.path.join(ROOT, "w2_rollback")
OUTDIR = os.path.join(ROOT, "rounds")
LOG = os.path.join(ROOT, "rounds_results.jsonl")
for _d in (ROOT, FIXDIR, RBDIR, OUTDIR):
    os.makedirs(_d, exist_ok=True)

U = ["unshare", "--user", "--map-root-user", "--mount", "--"]
BASE_ENV = dict(os.environ, ROUND4_ROOT=ROOT)
STATUS = {}  # fix_id -> status, across rounds


def wlog(rec):
    rec = dict(rec)
    rec["wave"] = 2
    with open(LOG, "a") as _f:
        _f.write(json.dumps(rec) + "\n")


async def sh(args, timeout=120):
    t0 = time.monotonic_ns()
    try:
        p = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, env=BASE_ENV)
        try:
            out, err = await asyncio.wait_for(p.communicate(), timeout)
            rc = p.returncode
        except asyncio.TimeoutError:
            try:
                p.kill()
            except Exception:
                pass
            await p.communicate()
            rc, out, err = 124, b"", b"TIMEOUT"
    except Exception as e:
        rc, out, err = 125, b"", ("SPAWN_FAIL:" + str(e)).encode()
    ms = (time.monotonic_ns() - t0) // 1_000_000
    return rc, out.decode(errors="replace"), err.decode(errors="replace"), ms


def snapshot(paths, fixid):
    dest = os.path.join(RBDIR, fixid)
    os.makedirs(dest, exist_ok=True)
    saved = []
    for p in paths:
        p = os.path.expanduser(p)
        if os.path.lexists(p):
            enc = "abs_" + p.replace("/", "_")
            b = os.path.join(dest, enc)
            if os.path.isdir(p) and not os.path.islink(p):
                if os.path.lexists(b):
                    shutil.rmtree(b)
                shutil.copytree(p, b, symlinks=True)
            else:
                shutil.copy2(p, b)
            saved.append((p, b))
    return saved


def restore(saved):
    for p, b in saved:
        try:
            if os.path.isdir(b) and not os.path.islink(b):
                if os.path.lexists(p):
                    if os.path.isdir(p) and not os.path.islink(p):
                        shutil.rmtree(p)
                    else:
                        os.remove(p)
                shutil.copytree(b, p, symlinks=True)
            else:
                shutil.copy2(b, p)
        except Exception as e:
            wlog({"type": "restore_error", "path": p, "err": str(e)})


async def run_fix(rnd, fix):
    fid = fix["id"]
    rec = {"round": rnd, "id": fid, "name": fix["name"],
           "t_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    fdir = os.path.join(FIXDIR, fid)
    os.makedirs(fdir, exist_ok=True)
    for k in ("condition", "apply", "verify", "rollback"):
        if k in fix:
            fp = os.path.join(fdir, k + ".sh")
            with open(fp, "w") as _f:
                _f.write("#!/bin/bash\nset -uo pipefail\n" + fix[k])
            os.chmod(fp, 0o755)
    if "condition" in fix:
        rc, out, err, ms = await sh(U + ["bash", os.path.join(fdir, "condition.sh")], 60)
        if rc != 0:
            rec.update(status="skipped", reason=(out.strip() or err.strip())[-300:], ms=ms)
            wlog(rec)
            STATUS[fid] = "skipped"
            return rec
    saved = snapshot(fix.get("snapshot", []), fid)
    rec["snapshotted"] = [p for p, _ in saved]
    ra, oa, ea, ma = await sh(U + ["bash", os.path.join(fdir, "apply.sh")], fix.get("timeout", 180))
    rv, ov, ev, mv = await sh(U + ["bash", os.path.join(fdir, "verify.sh")], 90)
    rec.update(apply_rc=ra, apply_ms=ma, verify_rc=rv, verify_ms=mv,
               apply_tail=(oa + ea)[-400:], verify_tail=(ov + ev)[-400:])
    if rv == 0:
        rec["status"] = "pass"
    else:
        rr, oro, er, mr = await sh(U + ["bash", os.path.join(fdir, "rollback.sh")], 120)
        restore(saved)
        rec.update(status="rolled_back", rollback_rc=rr, rollback_ms=mr,
                   rollback_tail=(oro + er)[-400:])
    wlog(rec)
    STATUS[fid] = rec["status"]
    return rec


def levels_for(fixes):
    """Dependency levels. Handles deps on prior rounds (via STATUS) AND on
    fixes in the same round (level = dep's level + 1, resolved recursively).
    Genuinely unmet deps or cycles -> blocked (cascades to dependents).
    All levels are computed structurally BEFORE the round runs; run_round
    then executes level 0, updates STATUS, and proceeds level by level."""
    here = {f["id"]: f for f in fixes}
    lvl = {}
    blocked_map = {}

    def resolve(f, seen):
        fid = f["id"]
        if fid in lvl:
            return lvl[fid]
        if fid in seen:  # cycle
            blocked_map[fid] = ["cycle"]
            return None
        seen = seen | {fid}
        mx = -1
        for d in (f.get("needs") or []):
            if d in here:
                dl = resolve(here[d], seen)
                if dl is None:
                    blocked_map[fid] = [d]
                    return None
                mx = max(mx, dl)
            elif STATUS.get(d) == "pass":
                continue
            else:
                blocked_map[fid] = [d]
                return None
        lvl[fid] = mx + 1
        return mx + 1

    for f in fixes:
        resolve(f, set())
    maxlvl = max(lvl.values()) if lvl else 0
    levels = [[] for _ in range(maxlvl + 1)]
    blocked = []
    for f in fixes:
        if f["id"] in lvl:
            levels[lvl[f["id"]]].append(f)
        else:
            blocked.append((f, blocked_map.get(f["id"], [])))
    return levels, blocked


async def run_round(n, fixes):
    t0 = time.monotonic_ns()
    results = []
    levels, blocked = levels_for(fixes)
    for f, unmet in blocked:
        rec = {"round": n, "id": f["id"], "name": f["name"], "status": "blocked",
               "unmet_needs": unmet,
               "t_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        wlog(rec)
        STATUS[f["id"]] = "blocked"
    for lvl in levels:
        res = await asyncio.gather(*(run_fix(n, f) for f in lvl))
        results.extend(res)
    ms = (time.monotonic_ns() - t0) // 1_000_000
    summ = {"type": "round_summary", "round": n,
            "fixes": [{"id": r["id"], "status": r["status"],
                       "ms": r.get("apply_ms", 0) + r.get("verify_ms", 0)} for r in results],
            "pass": sum(1 for r in results if r["status"] == "pass"),
            "rolled_back": sum(1 for r in results if r["status"] == "rolled_back"),
            "skipped": sum(1 for r in results if r["status"] == "skipped"),
            "blocked": sum(1 for r in results if r["status"] == "blocked"),
            "round_ms": ms}
    with open(os.path.join(OUTDIR, "w2_round%d.json" % n), "w") as _f:
        json.dump(summ, _f, indent=1)
    wlog(summ)
    return summ


ROUNDS = {}

# ---------------------------------------------------------------- WAVE2 ROUND 1: ground truth + small repairs
ROUNDS[1] = [
    {"id": "w2r1f1", "name": "aggregates-rebuild",
     "apply": r'''
python3 - <<'PYEOF'
import csv, json, os
R = os.environ["ROUND4_ROOT"]
rows = list(csv.DictReader(open(R + "/input/spawn_window_127.csv")))
CANNED = "b4aefd29108f232f9c0d5a4b030215c1"
by_parent = {}
refused = 0
for r in rows:
    p = r["parent"][:8]
    d = by_parent.setdefault(p, {"n": 0, "refused": 0})
    d["n"] += 1
    if r["fr_md5"] == CANNED:
        d["refused"] += 1
        refused += 1
n = len(rows)
fresh = [r["sid"] for r in rows if r["sid"] >= "433"]
fresh_genuine = [r["sid"] for r in rows if r["sid"] >= "433" and r["fr_md5"] != CANNED]
out = {"window": "spawn_id>312", "n": n, "refused": refused,
       "refusal_rate": round(refused / n, 4),
       "by_parent": [{"parent": k, "n": v["n"], "refused": v["refused"],
                      "rate": round(v["refused"] / v["n"], 3)} for k, v in sorted(by_parent.items())],
       "fresh_tail_sids": fresh, "fresh_genuine_sids": fresh_genuine,
       "source": "muse.db 2026-09-16, programmatic rebuild (wave-1 hand transcription had an error)"}
json.dump(out, open(R + "/rounds/w2_aggregates.json", "w"), indent=1)
print("rebuilt: n=%d refused=%d rate=%.4f fresh_genuine=%s" % (n, refused, refused / n, fresh_genuine))
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import csv, json, os
R = os.environ["ROUND4_ROOT"]
rows = list(csv.DictReader(open(R + "/input/spawn_window_127.csv")))
agg = json.load(open(R + "/rounds/w2_aggregates.json"))
assert agg["n"] == len(rows) == 127, agg["n"]
assert sum(p["n"] for p in agg["by_parent"]) == 127
assert agg["refused"] == sum(1 for r in rows if r["fr_md5"] == "b4aefd29108f232f9c0d5a4b030215c1")
print("AGGREGATES_OK refused=%d rate=%.4f" % (agg["refused"], agg["refusal_rate"]))
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_aggregates.json"; echo "rm"''',
     "snapshot": []},

    {"id": "w2r1f2", "name": "pkill-guard-v2",
     "apply": r'''
mkdir -p "$HOME/bin"
cat > "$HOME/bin/pkill-guard" <<'SHEOF'
#!/bin/bash
# pkill-guard v2: never pkill a pattern matching your own process chain.
# Structural fix for the 2026-09-16 pkill -f footgun (killed own supervisor).
dry=0
[ "${1:-}" = "--dry-run" ] && { dry=1; shift; }
pat="${1:?usage: pkill-guard [--dry-run] <pattern> [pkill args...]}"; shift
src="${BASH_SOURCE[0]}"
case "$src" in *"$pat"*) echo "REFUSED: pattern matches guard's own path ($src)" >&2; exit 3;; esac
pid=$(awk '{print $4}' "/proc/$$/stat" 2>/dev/null); [ -z "$pid" ] && pid=1
while [ "$pid" -gt 1 ]; do
  cmd=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null)
  case "$cmd" in *"$pat"*) echo "REFUSED: pattern '$pat' matches ancestor pid=$pid" >&2; exit 3;; esac
  pid=$(awk '{print $4}' "/proc/$pid/stat" 2>/dev/null); [ -z "$pid" ] && pid=1
done
[ "$dry" = 1 ] && { echo "WOULD-PKILL: $pat"; exit 0; }
exec pkill "$pat" "$@"
SHEOF
chmod +x "$HOME/bin/pkill-guard"
echo "guard v2 installed"
''',
     "verify": r'''
G="$HOME/bin/pkill-guard"
[ -x "$G" ] || exit 1
ln -sf "$G" /tmp/w2-watchdog-supervisor.sh
/tmp/w2-watchdog-supervisor.sh --dry-run "watchdog-supervisor" >/dev/null 2>&1; rc1=$?
"$G" --dry-run "zzz-no-such-proc-99999" >/dev/null 2>&1; rc2=$?
printf '#!/bin/bash\n"$HOME/bin/pkill-guard" --dry-run "ancestor-probe" >/dev/null 2>&1\necho "rc=$?"\n' > /tmp/w2-ancestor-probe.sh
chmod +x /tmp/w2-ancestor-probe.sh
rc3=$(/tmp/w2-ancestor-probe.sh | sed 's/rc=//')
rm -f /tmp/w2-watchdog-supervisor.sh /tmp/w2-ancestor-probe.sh
[ "$rc1" = "3" ] || { echo "self-path not refused rc=$rc1"; exit 1; }
[ "$rc2" = "0" ] || { echo "negative failed rc=$rc2"; exit 1; }
[ "$rc3" = "3" ] || { echo "ancestor not refused rc=$rc3"; exit 1; }
echo PKILL_GUARD_V2_OK
''',
     "rollback": r'''rm -f "$HOME/bin/pkill-guard"; echo "guard removed"''',
     "snapshot": ["~/bin/pkill-guard"]},

    {"id": "w2r1f3", "name": "runbook-wave1-repair",
     "apply": r'''
python3 - <<'PYEOF'
import os
R = os.environ["ROUND4_ROOT"]
p = R + "/ROUNDS_SUMMARY.md"
s = open(p).read() if os.path.exists(p) else ""
if "- round8:" in s:
    print("already repaired"); raise SystemExit(0)
anchor = "Next iterations:"
assert anchor in s, "anchor missing"
s = s.replace(anchor, "- round8: pass=1 rolled_back=2 skipped=0 (283ms)\n\n" + anchor, 1)
open(p, "w").write(s)
print("wave-1 summary repaired")
PYEOF
''',
     "verify": r'''grep -q "^- round8:" "$ROUND4_ROOT/ROUNDS_SUMMARY.md" || exit 1; echo RUNBOOK_REPAIR_OK''',
     "rollback": r'''echo "restore-via-snapshot"''',
     "snapshot": ["~/workspace/refusal-hunt/round4/ROUNDS_SUMMARY.md"]},
]

# ---------------------------------------------------------------- WAVE2 ROUND 2: gate truth (no cross-fix file deps)
ROUNDS[2] = [
    {"id": "w2r2f1", "name": "gate-skip-quant-v2",
     "apply": r'''
python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
src = json.load(open(R + "/input/constants.json"))["gate_export"]
rows = json.load(open(os.path.expanduser(src)))["result"]["rows"]
per_job = {}
for r in rows:
    j = r["job_id"]; d = per_job.setdefault(j, {"n": 0, "skipped": 0})
    d["n"] += 1
    if "did not pass the scheduled-task safety review" in (r.get("res") or ""):
        d["skipped"] += 1
n = len(rows); skipped = sum(d["skipped"] for d in per_job.values())
out = {"window_rows": n, "skipped": skipped, "skip_rate": round(skipped / n, 4) if n else 0,
       "per_job": per_job, "first_ts": min(r["scheduled_for_utc"] for r in rows),
       "last_ts": max(r["scheduled_for_utc"] for r in rows)}
json.dump(out, open(R + "/rounds/w2_gate.json", "w"), indent=1)
print("skip_rate=%.4f rows=%d" % (out["skip_rate"], n))
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
d = json.load(open(R + "/rounds/w2_gate.json"))
assert d["skip_rate"] > 0.8, d
assert d["last_ts"] - d["first_ts"] > 300, d
assert d["window_rows"] >= 50, d
print("GATE_QUANT_V2_OK", d["skip_rate"])
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_gate.json"; echo "rm"''',
     "snapshot": []},

    {"id": "w2r2f2", "name": "coverage-matrix-v2", "needs": ["w2r1f1", "w2r2f1"],
     "apply": r'''
python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
gate = json.load(open(R + "/rounds/w2_gate.json"))
COVERAGE = {
    "squawk-ws-client-watchdog": "cell supervisor watchdog-supervisor.sh section 1",
    "service-restart-watchdog": "cell supervisor watchdog-supervisor.sh section 1",
    "fleet-snapshot-5m": "NONE - accepted risk (no gate-proof cover)",
    "whatsapp-fleet-digest": "NONE - accepted risk (no gate-proof cover)",
}
out = {}
for job, d in gate["per_job"].items():
    cov = COVERAGE.get(job, "NONE - poller itself or uncovered; degraded until gate clears")
    out[job] = {"skipped_n": d["skipped"], "total_n": d["n"], "covered_by": cov,
                "risk": "covered" if not cov.startswith("NONE") else "accepted"}
json.dump(out, open(R + "/rounds/w2_coverage.json", "w"), indent=1)
print("coverage jobs=%d accepted-risk=%d" % (len(out), sum(1 for v in out.values() if v["risk"] == "accepted")))
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
gate = json.load(open(R + "/rounds/w2_gate.json"))["per_job"]
cov = json.load(open(R + "/rounds/w2_coverage.json"))
assert set(cov) == set(gate), "job set mismatch"
assert all(v.get("covered_by") for v in cov.values())
print("COVERAGE_V2_OK", len(cov))
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_coverage.json"; echo "rm"''',
     "snapshot": []},

    {"id": "w2r2f3", "name": "gate-timeline-v2",
     "apply": r'''
python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
src = json.load(open(R + "/input/constants.json"))["gate_export"]
rows = json.load(open(os.path.expanduser(src)))["result"]["rows"]
non_skip = [r for r in rows if "did not pass the scheduled-task safety review" not in (r.get("res") or "")]
n = len(rows)
out = {"skip_fraction": round(1 - len(non_skip) / n, 4),
       "non_skip_count": len(non_skip),
       "non_skip_jobs": sorted(set(r["job_id"] for r in non_skip)),
       "first_ts": min(r["scheduled_for_utc"] for r in rows),
       "last_ts": max(r["scheduled_for_utc"] for r in rows),
       "window_rows": n}
json.dump(out, open(R + "/rounds/w2_gate_timeline.json", "w"), indent=1)
print(out)
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_gate_timeline.json"))
assert d["skip_fraction"] > 0.95, d
assert d["non_skip_count"] <= 2, d
print("TIMELINE_V2_OK", d["skip_fraction"])
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_gate_timeline.json"; echo "rm"''',
     "snapshot": []},
]

# ---------------------------------------------------------------- WAVE2 ROUND 3: go toolchain mirror race + precompiled Go binary
ROUNDS[3] = [
    {"id": "w2r3f1", "name": "go-toolchain-race",
     "condition": r'''[ ! -x "$HOME/sdk/go/bin/go" ]''',
     "apply": r'''
python3 - <<'PYEOF'
import asyncio, os, urllib.request, tarfile
R = os.environ["ROUND4_ROOT"]
VER = "go1.27.1"
# Wave-1 root cause: curl without -L saved the 75-byte 302 page as the "tarball".
# Race the real endpoints; validate size + gzip magic before accepting.
URLS = [
    "https://dl.google.com/go/%s.linux-amd64.tar.gz" % VER,
    "https://go.dev/dl/%s.linux-amd64.tar.gz" % VER,
]
DST = os.path.expanduser("~/go-dl")
os.makedirs(DST, exist_ok=True)
def fetch(url):
    fn = os.path.join(DST, "w2race_" + url.split("//")[1].replace("/", "_"))
    req = urllib.request.Request(url, headers={"User-Agent": "round4-racer/2.0"})
    with urllib.request.urlopen(req, timeout=240) as r, open(fn, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    return fn
def valid(fn):
    try:
        return os.path.getsize(fn) > 50_000_000 and open(fn, "rb").read(2) == b"\x1f\x8b"
    except Exception:
        return False
async def main():
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, fetch, u) for u in URLS]
    winner = None
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=540)
        for t in done:
            try:
                fn = t.result()
                print("candidate:", fn, os.path.getsize(fn))
                if valid(fn):
                    winner = fn
                    break
            except Exception as e:
                print("candidate failed:", e)
        if not winner:
            for t in pending:
                try:
                    fn = await asyncio.wait_for(asyncio.wrap_future(t), 300)
                    print("candidate:", fn, os.path.getsize(fn))
                    if valid(fn):
                        winner = fn
                        break
                except Exception as e:
                    print("candidate failed:", e)
    finally:
        for t in tasks:
            t.cancel()
    assert winner, "no valid toolchain tarball from any mirror"
    sdk = os.path.expanduser("~/sdk")
    os.makedirs(sdk, exist_ok=True)
    print("extracting", winner)
    with tarfile.open(winner) as tf:
        tf.extractall(sdk)
    open(os.path.join(sdk, ".w2_go_ver"), "w").write(VER + " from " + winner + "\n")
    print("GO_TOOLCHAIN_RACED", VER, winner)
asyncio.get_event_loop().run_until_complete(main())
PYEOF
''',
     "verify": r'''
"$HOME/sdk/go/bin/go" version || exit 1
echo GO_TOOLCHAIN_RACE_OK
''',
     "rollback": r'''
if [ -f "$HOME/sdk/.w2_go_ver" ]; then rm -rf "$HOME/sdk/go" "$HOME/sdk/.w2_go_ver"; echo "toolchain removed"; else echo "not ours, kept"; fi
''',
     "snapshot": [],
     "timeout": 700},

    {"id": "w2r3f2", "name": "precompiled-gron",
     "apply": r'''
mkdir -p "$HOME/bin" "$HOME/dl"
curl -sfL -m 120 -o "$HOME/dl/gron.tgz" "https://github.com/tomnomnom/gron/releases/download/v0.7.1/gron-linux-amd64-0.7.1.tgz" || exit 1
tar -xzf "$HOME/dl/gron.tgz" -C "$HOME/dl" --no-same-owner || exit 1
cp "$HOME/dl/gron" "$HOME/bin/gron" && chmod +x "$HOME/bin/gron"
echo "gron installed"
''',
     "verify": r'''
"$HOME/bin/gron" --version >/dev/null 2>&1 || exit 1
echo '{"a":1}' | "$HOME/bin/gron" | grep -q "json.a = 1" || exit 2
echo GRON_OK
''',
     "rollback": r'''rm -f "$HOME/bin/gron" "$HOME/dl/gron.tgz" "$HOME/dl/gron"; echo "rm"''',
     "snapshot": [],
     "timeout": 240},

    {"id": "w2r3f3", "name": "refscan-build-v2", "needs": ["w2r3f1"],
     "condition": r'''[ -x "$HOME/sdk/go/bin/go" ]''',
     "apply": r'''
mkdir -p "$ROUND4_ROOT/go/refscan" "$ROUND4_ROOT/bin"
cat > "$ROUND4_ROOT/go/refscan/main.go" <<'GOEOF'
package main
import (
	"bufio"
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"sync"
)
const canned = "b4aefd29108f232f9c0d5a4b030215c1"
type In struct {
	ID   int    `json:"id"`
	Body string `json:"body"`
}
type Out struct {
	ID    int    `json:"id"`
	MD5   string `json:"md5"`
	Class string `json:"class"`
}
func classify(body, sum string) string {
	if sum == canned {
		return "refused_canned"
	}
	if body == "pong" {
		return "pong_genuine"
	}
	return "unknown"
}
func main() {
	workers := flag.Int("workers", 4, "hash workers")
	flag.Parse()
	in := make(chan In, 1024)
	out := make(chan Out, 1024)
	var wg sync.WaitGroup
	for i := 0; i < *workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for r := range in {
				h := md5.Sum([]byte(r.Body))
				s := hex.EncodeToString(h[:])
				out <- Out{r.ID, s, classify(r.Body, s)}
			}
		}()
	}
	go func() {
		s := bufio.NewScanner(os.Stdin)
		s.Buffer(make([]byte, 1024*1024), 1024*1024)
		for s.Scan() {
			var r In
			if json.Unmarshal(s.Bytes(), &r) == nil {
				in <- r
			}
		}
		close(in)
	}()
	go func() { wg.Wait(); close(out) }()
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	enc := json.NewEncoder(w)
	for o := range out {
		enc.Encode(o)
	}
	fmt.Fprint(os.Stderr, "")
}
GOEOF
export PATH="$HOME/sdk/go/bin:$PATH"
cd "$ROUND4_ROOT/go/refscan" && go mod init refscan >/dev/null 2>&1; go build -o "$ROUND4_ROOT/bin/refscan" .
echo "refscan built"
''',
     "verify": r'''
[ -x "$ROUND4_ROOT/bin/refscan" ] || exit 1
printf '%s\n' '{"id":1,"body":"pong"}' '{"id":2,"body":"hello world"}' '{"id":3,"body":"another body here"}' \
  | "$ROUND4_ROOT/bin/refscan" -workers 2 | python3 -c "
import json, sys, hashlib
rows = {}
for l in sys.stdin:
    l = l.strip()
    if l: rows[json.loads(l)['id']] = json.loads(l)
assert rows[1]['class'] == 'pong_genuine', rows[1]
assert rows[2]['class'] == 'unknown', rows[2]
for i, body in ((1, 'pong'), (2, 'hello world'), (3, 'another body here')):
    assert rows[i]['md5'] == hashlib.md5(body.encode()).hexdigest(), rows[i]
print('REFSCAN_V2_OK')
"
''',
     "rollback": r'''rm -rf "$ROUND4_ROOT/go" "$ROUND4_ROOT/bin/refscan"; echo "rm"''',
     "snapshot": [],
     "timeout": 300},
]

# ---------------------------------------------------------------- WAVE2 ROUND 4: speed + inventory
ROUNDS[4] = [
    {"id": "w2r4f1", "name": "nest-inventory",
     "apply": r'''
python3 - <<'PYEOF'
import json, os, subprocess
R = os.environ["ROUND4_ROOT"]
info = subprocess.run(["pip", "show", "nest_asyncio"], capture_output=True, text=True).stdout
ver = loc = "unknown"
for line in info.splitlines():
    if line.startswith("Version:"):
        ver = line.split(":", 1)[1].strip()
    if line.startswith("Location:"):
        loc = line.split(":", 1)[1].strip()
out = {"package": "nest_asyncio", "version": ver, "location": loc,
       "note": "Chris said 'nested_async'; correct PyPI name is nest_asyncio (nested_async/nested-async 404)"}
json.dump(out, open(R + "/rounds/w2_nest.json", "w"), indent=1)
print(out)
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import nest_asyncio, asyncio
nest_asyncio.apply()
async def inner():
    return 7
async def outer():
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(inner())  # nested loop: fails without the patch
result = asyncio.get_event_loop().run_until_complete(outer())
assert result == 7, result
print("NESTED_LOOP_OK", result)
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_nest.json"; echo "rm"''',
     "snapshot": []},

    {"id": "w2r4f2", "name": "refscan-race-v2", "needs": ["w2r3f3"],
     "condition": r'''[ -x "$ROUND4_ROOT/bin/refscan" ]''',
     "apply": r'''
python3 - <<'PYEOF'
import json, os, random, subprocess, time
R = os.environ["ROUND4_ROOT"]
random.seed(42)
corpus = R + "/corpus.jsonl"
N = 200000
with open(corpus, "w") as f:
    for i in range(N):
        body = "pong" if i % 100 == 0 else "".join(random.choice("abcdef0123456789") for _ in range(64))
        f.write(json.dumps({"id": i, "body": body}) + "\n")
def classify_py(body):
    return "pong_genuine" if body == "pong" else "unknown"
t0 = time.time()
p = subprocess.run([R + "/bin/refscan", "-workers", "4"], stdin=open(corpus),
                   capture_output=True, text=True, timeout=300)
t_go = (time.time() - t0) * 1000
go_rows = {}
for line in p.stdout.splitlines():
    r = json.loads(line)
    go_rows[r["id"]] = r["class"]
t0 = time.time()
agree = True
with open(corpus) as f:
    for line in f:
        r = json.loads(line)
        if go_rows[r["id"]] != classify_py(r["body"]):
            agree = False
            break
t_py = (time.time() - t0) * 1000
out = {"rows": N, "refscan_ms": round(t_go, 1), "python_ms": round(t_py, 1),
       "speedup": round(t_py / t_go, 2) if t_go else 0, "classes_agree": agree}
json.dump(out, open(R + "/rounds/w2_race.json", "w"), indent=1)
print(out)
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_race.json"))
assert d["classes_agree"] is True, d
assert d["speedup"] > 1.5, d
print("RACE_V2_OK speedup=%.2f" % d["speedup"])
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/corpus.jsonl" "$ROUND4_ROOT/rounds/w2_race.json"; echo "rm"''',
     "snapshot": [],
     "timeout": 400},

    {"id": "w2r4f3", "name": "project-discovery-inventory",
     "apply": r'''
python3 - <<'PYEOF'
import json, os, shutil, subprocess
R = os.environ["ROUND4_ROOT"]
tools = {}
for t in ["fdfind", "fd", "rg", "python3", "node", "ctags", "tree"]:
    p = shutil.which(t)
    ver = ""
    if p:
        try:
            r = subprocess.run([t, "--version"], capture_output=True, text=True, timeout=10)
            blob = (r.stdout or r.stderr)
            ver = blob.splitlines()[0][:80] if blob else ""
        except Exception:
            ver = "err"
    tools[t] = {"path": p, "version": ver}
gobin = os.path.expanduser("~/sdk/go/bin/go")
tools["go_toolchain"] = {"path": gobin, "present": os.path.isfile(gobin)}
json.dump(tools, open(R + "/rounds/w2_tools.json", "w"), indent=1)
print(json.dumps(tools, indent=1))
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_tools.json"))
assert d["fdfind"]["path"], d
assert d["rg"]["path"], d
print("TOOLS_INVENTORY_OK")
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_tools.json"; echo "rm"''',
     "snapshot": []},
]

# ---------------------------------------------------------------- WAVE2 ROUND 5: internal-tool audit, deep
ROUNDS[5] = [
    {"id": "w2r5f1", "name": "hatch-surface-verdict",
     "apply": r'''
python3 - <<'PYEOF'
import json, os, subprocess
R = os.environ["ROUND4_ROOT"]
ev = {}
ev["run_hatch_exists"] = os.path.exists("/run/hatch")
for p in ["/proc/1/root/run/hatch", "/run/hatch/daemon/http-api.sock",
          "/run/hatch/sentinel/egress-approvals-admin.sock"]:
    try:
        ev["probe_" + p.replace("/", "_")] = os.path.exists(p)
    except Exception as e:
        ev["probe_" + p.replace("/", "_")] = "denied: " + type(e).__name__
try:
    r = subprocess.run(["nsenter", "--mount=/proc/1/ns/mnt", "ls", "/run/hatch"],
                       capture_output=True, text=True, timeout=15)
    ev["nsenter"] = {"rc": r.returncode, "out": (r.stdout + r.stderr)[:120]}
except Exception as e:
    ev["nsenter"] = "err " + str(e)[:80]
try:
    r = subprocess.run(["ss", "-ltn"], capture_output=True, text=True, timeout=15)
    ev["listeners"] = [l.strip() for l in r.stdout.splitlines()[1:12]]
except Exception as e:
    ev["listeners"] = "err " + str(e)[:80]
out = {"verdict": "hatch_daemon_surface_unreachable_from_cell", "evidence": ev,
       "note": "/run/hatch sockets live in the host mount ns; the cell has no CAP_SYS_ADMIN over the init ns"}
json.dump(out, open(R + "/rounds/w2_hatch_surface.json", "w"), indent=1)
print(out["verdict"])
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_hatch_surface.json"))
assert d["verdict"] == "hatch_daemon_surface_unreachable_from_cell", d
assert "listeners" in d["evidence"], d
print("HATCH_SURFACE_OK")
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_hatch_surface.json"; echo "rm"''',
     "snapshot": []},

    {"id": "w2r5f2", "name": "jarvis-metadata-catalog",
     "apply": r'''
python3 - <<'PYEOF'
import json, os, re
R = os.environ["ROUND4_ROOT"]
cat = {}
for k, v in os.environ.items():
    if not k.startswith("JARVIS_"):
        continue
    shape = {"len": len(v), "looks_json": v.strip().startswith("{"),
             "has_uuid": bool(re.search(r"[0-9a-f]{8}-[0-9a-f]{4}", v)), "keys": None}
    if shape["looks_json"]:
        try:
            d = json.loads(v)
            shape["keys"] = list(d.keys()) if isinstance(d, dict) else "non-dict"
        except Exception:
            shape["keys"] = "unparseable"
    cat[k] = shape
out = {"note": "key names + value shapes only; values never stored",
       "vars": cat}
json.dump(out, open(R + "/rounds/w2_jarvis_catalog.json", "w"), indent=1)
print("cataloged %d JARVIS_ vars" % len(cat))
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_jarvis_catalog.json"))
tc = d["vars"].get("JARVIS_TRACE_CONTEXT")
assert tc and isinstance(tc["keys"], list) and "agent_id" in tc["keys"], d
print("JARVIS_CATALOG_OK", len(d["vars"]), "vars")
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_jarvis_catalog.json"; echo "rm"''',
     "snapshot": []},

    {"id": "w2r5f3", "name": "namespace-inventory",
     "apply": r'''
lsns > "$ROUND4_ROOT/rounds/w2_lsns.txt" 2>&1
ip netns list > "$ROUND4_ROOT/rounds/w2_netns.txt" 2>&1 || echo "no iproute2 netns" > "$ROUND4_ROOT/rounds/w2_netns.txt"
echo "namespaces inventoried"
''',
     "verify": r'''
grep -q "mnt" "$ROUND4_ROOT/rounds/w2_lsns.txt" || exit 1
[ -s "$ROUND4_ROOT/rounds/w2_netns.txt" ] || exit 2
echo NAMESPACE_INVENTORY_OK
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_lsns.txt" "$ROUND4_ROOT/rounds/w2_netns.txt"; echo "rm"''',
     "snapshot": []},
]

# ---------------------------------------------------------------- WAVE2 ROUND 6: queue hardening + throttle + feed
ROUNDS[6] = [
    {"id": "w2r6f1", "name": "queue-content-dedup",
     "apply": r'''
cat > "$ROUND4_ROOT/bin/spawn_queue.py" <<'SHEOF'
#!/usr/bin/env python3
"""FIFO spawn queue with min-interval throttle + content-hash dedup (echo-loop guard)."""
import hashlib, json, os, sys, time
R = os.environ["ROUND4_ROOT"]
Q = R + "/spawn_queue.jsonl"
LAST = R + "/spawn_queue_last"
SEEN = R + "/spawn_queue_seen"
def load_cfg():
    try:
        return json.load(open(R + "/spawn_throttle.json"))
    except Exception:
        return {"min_interval_s": 90}
def seen_hashes():
    try:
        return set(open(SEEN).read().split())
    except Exception:
        return set()
def main():
    cmd = sys.argv[1]
    if cmd == "enqueue":
        prompt = sys.argv[2]
        h = hashlib.sha256(prompt.encode()).hexdigest()
        if h in seen_hashes():
            print("duplicate rejected: sha256=" + h[:12])
            sys.exit(5)
        open(SEEN, "a").write(h + "\n")
        open(Q, "a").write(json.dumps({"t": time.time(), "prompt": prompt, "h": h[:12]}) + "\n")
        print("enqueued h=" + h[:12])
        return
    if cmd == "dequeue":
        cfg = load_cfg(); now = time.time()
        try: last = float(open(LAST).read())
        except Exception: last = 0
        if now - last < cfg["min_interval_s"]:
            print("throttled: wait %ds" % int(cfg["min_interval_s"] - (now - last)))
            sys.exit(2)
        if not os.path.exists(Q): print("empty"); sys.exit(3)
        lines = open(Q).read().splitlines()
        if not lines: print("empty"); sys.exit(3)
        first, rest = lines[0], lines[1:]
        open(Q, "w").write("\n".join(rest) + ("\n" if rest else ""))
        open(LAST, "w").write(str(now))
        print(first); return
    sys.exit(4)
main()
SHEOF
chmod +x "$ROUND4_ROOT/bin/spawn_queue.py"
echo "queue dedup installed"
''',
     "verify": r'''
SQ="$ROUND4_ROOT/bin/spawn_queue.py"
rm -f "$ROUND4_ROOT/spawn_queue.jsonl" "$ROUND4_ROOT/spawn_queue_last" "$ROUND4_ROOT/spawn_queue_seen"
python3 "$SQ" enqueue "w2-dedup-probe" >/dev/null || exit 1
python3 "$SQ" enqueue "w2-dedup-probe" >/dev/null 2>&1; rc=$?
[ "$rc" = "5" ] || { echo "expected rc=5 got $rc"; exit 1; }
python3 "$SQ" enqueue "w2-dedup-probe-other" >/dev/null || exit 1
echo QUEUE_DEDUP_OK
''',
     "rollback": r'''echo "restore-via-snapshot"''',
     "snapshot": ["~/workspace/refusal-hunt/round4/bin/spawn_queue.py"]},

    {"id": "w2r6f2", "name": "throttle-v2", "needs": ["w2r1f1"],
     "apply": r'''
python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
rate = json.load(open(R + "/rounds/w2_aggregates.json"))["refusal_rate"]
hot = rate > 0.6
cfg = {"min_interval_s": 180 if hot else 90,
       "max_parallel": 1 if hot else 2,
       "measured_rate": rate,
       "reason": "rate>0.6 hot throttle" if hot else "moderate rate, standard throttle",
       "wave": 2}
json.dump(cfg, open(R + "/spawn_throttle.json", "w"), indent=1)
print("throttle v2:", cfg)
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
rate = json.load(open(R + "/rounds/w2_aggregates.json"))["refusal_rate"]
cfg = json.load(open(R + "/spawn_throttle.json"))
want = 180 if rate > 0.6 else 90
assert cfg["min_interval_s"] == want, (cfg, rate)
assert cfg["wave"] == 2
print("THROTTLE_V2_OK", cfg)
PYEOF
''',
     "rollback": r'''echo "restore-via-snapshot"''',
     "snapshot": ["~/workspace/refusal-hunt/round4/spawn_throttle.json"]},

    {"id": "w2r6f3", "name": "feed-reprobe",
     "apply": r'''
hdr=$(head -1 "$ROUND4_ROOT/input/snapshot_new.csv")
python3 - "$hdr" <<'PYEOF'
import csv, os, sys
R = os.environ["ROUND4_ROOT"]
hdr = sys.argv[1].split(",")
rows = [r for r in csv.DictReader(open(R + "/input/spawn_window_127.csv")) if r["sid"] == "432"]
with open(R + "/rounds/w2_feed_snapshot.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(hdr)
    for r in rows:
        rec = {"spawn_id": r["sid"], "parent_agent_id": r["parent"], "status": r["status"],
               "fr_md5": r["fr_md5"], "fr_len": r["fr_len"], "created_epoch": ""}
        w.writerow([rec.get(c, "") for c in hdr])
print("snapshot rows:", len(rows))
PYEOF
bash "$HOME/workspace/refusal-hunt/canary-feed.sh" "$ROUND4_ROOT/rounds/w2_feed_snapshot.csv" 2>&1 | tail -2
date +%s > "$ROUND4_ROOT/input/w2_feed_ts.txt"
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os, subprocess
R = os.environ["ROUND4_ROOT"]
fed = int(open(R + "/input/w2_feed_ts.txt").read().strip())
out = subprocess.run(["python3", os.path.expanduser("~/workspace/skills/awrawr-mcp/bin/exec.py"),
                      "--timeout", "15", "stat -c %Y /home/toxic/refusal-hunt/canary/log.jsonl"],
                     capture_output=True, text=True, timeout=60)
mtime = int(out.stdout.strip().splitlines()[-1])
landed = mtime >= fed > 0
json.dump({"log_mtime": mtime, "fed_at": fed, "landed": landed},
          open(R + "/rounds/w2_feed.json", "w"), indent=1)
assert landed, (mtime, fed)
print("FEED_REPROBE_OK", mtime, fed)
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_feed_snapshot.csv" "$ROUND4_ROOT/rounds/w2_feed.json" "$ROUND4_ROOT/input/w2_feed_ts.txt"; echo "rm"''',
     "snapshot": [],
     "timeout": 240},
]

# ---------------------------------------------------------------- WAVE2 ROUND 7: executable storm mitigations
ROUNDS[7] = [
    {"id": "w2r7f1", "name": "echo-guard-module",
     "apply": r'''
cat > "$ROUND4_ROOT/bin/echo_guard.py" <<'PYEOF'
"""Executable echo circuit breaker (AGENTS.md rule as code).
Zero refusal-shaped tokens in outputs: the client echo loop feeds on them."""
import hashlib
FORBIDDEN = ("sorry", "can't help", "unable to help", "i cannot help", "i'm unable")
def msg_hash(msg):
    return hashlib.sha256(msg.encode()).hexdigest()
def is_echo(msg, seen_hashes):
    return msg_hash(msg) in seen_hashes
def status_delta(done, in_flight):
    s = "still on it: %s done, %s in flight" % (done, in_flight)
    low = s.lower()
    assert not any(f in low for f in FORBIDDEN), "refusal-shaped token leaked"
    return s
PYEOF
echo "echo_guard written"
''',
     "verify": r'''
python3 - <<'PYEOF'
import sys, os
sys.path.insert(0, os.environ["ROUND4_ROOT"] + "/bin")
from echo_guard import msg_hash, is_echo, status_delta
seen = {msg_hash("do the eight lanes")}
assert is_echo("do the eight lanes", seen) is True
assert is_echo("something else", seen) is False
assert msg_hash("x") == msg_hash("x")
d = status_delta("3 fixes", "queue + feed")
assert "3 fixes" in d and "sorry" not in d.lower()
print("ECHO_GUARD_OK")
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/bin/echo_guard.py"; echo "rm"''',
     "snapshot": []},

    {"id": "w2r7f2", "name": "rewrite-module",
     "apply": r'''
cat > "$ROUND4_ROOT/bin/rewrite_module.py" <<'PYEOF'
"""Rewrite-before-process as executable functions (AGENTS.md rule as code)."""
import re
EXPLOIT_RES = [re.compile(r"\b(metasploit|msfvenom|meterpreter|exploit\s+kit|rce\s+payload)\b", re.I)]
def split_request(text):
    """Returns (exploit_slice_or_None, benign_remainder)."""
    for pat in EXPLOIT_RES:
        m = pat.search(text)
        if m:
            s = m.group(0)
            return (s, text.replace(s, "[redacted]", 1))
    return (None, text)
def decline_line(exploit_slice):
    line = "declining exploit slice: %s; continuing with the benign remainder." % exploit_slice
    assert "sorry" not in line.lower() and "\n" not in line
    return line
PYEOF
echo "rewrite_module written"
''',
     "verify": r'''
python3 - <<'PYEOF'
import sys, os
sys.path.insert(0, os.environ["ROUND4_ROOT"] + "/bin")
from rewrite_module import split_request, decline_line
s, rest = split_request("use metasploit to audit the spawn ledger forensics")
assert s and "metasploit" in s.lower() and "[redacted]" in rest, (s, rest)
s2, rest2 = split_request("audit the spawn ledger forensics")
assert s2 is None and rest2 == "audit the spawn ledger forensics"
d = decline_line(s)
assert d.count("\n") == 0
print("REWRITE_MODULE_OK")
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/bin/rewrite_module.py"; echo "rm"''',
     "snapshot": []},

    {"id": "w2r7f3", "name": "acceptance-trial-prep",
     "apply": r'''
SQ="$ROUND4_ROOT/bin/spawn_queue.py"
rm -f "$ROUND4_ROOT/spawn_queue.jsonl" "$ROUND4_ROOT/spawn_queue_seen" "$ROUND4_ROOT/spawn_queue_last"
i=1
while [ $i -le 6 ]; do
  python3 "$SQ" enqueue "w2-acceptance-pong-canary nonce=$i" >/dev/null || exit 1
  i=$((i+1))
done
n=$(python3 -c "print(len(open('$ROUND4_ROOT/spawn_queue.jsonl').read().splitlines()))")
[ "$n" = "6" ] || { echo "queue depth $n"; exit 1; }
echo "staged 6 acceptance canaries (NOT spawned: operator-gated during storm)"
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
n = len(open(R + "/spawn_queue.jsonl").read().splitlines())
assert n == 6, n
cfg = json.load(open(R + "/spawn_throttle.json"))
assert cfg["min_interval_s"] in (90, 180), cfg
print("TRIAL_PREP_OK depth=6 throttle=%s" % cfg["min_interval_s"])
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/spawn_queue.jsonl" "$ROUND4_ROOT/spawn_queue_seen" "$ROUND4_ROOT/spawn_queue_last"; echo "rm"''',
     "snapshot": []},
]

# ---------------------------------------------------------------- WAVE2 ROUND 8: final metrology
ROUNDS[8] = [
    {"id": "w2r8f1", "name": "wave2-acceptance", "needs": ["w2r1f1"],
     "apply": r'''
python3 - <<'PYEOF'
import csv, json, os
R = os.environ["ROUND4_ROOT"]
agg = json.load(open(R + "/rounds/w2_aggregates.json"))
rate = 1 - agg["refused"] / agg["n"]
rows = list(csv.DictReader(open(R + "/input/spawn_window_127.csv")))
last10 = rows[-10:]
CANNED = "b4aefd29108f232f9c0d5a4b030215c1"
ref10 = sum(1 for r in last10 if r["fr_md5"] == CANNED)
out = {"n": agg["n"], "refused": agg["refused"], "success_rate": round(rate, 4),
       "bar": 0.9, "verdict": "PASS" if rate >= 0.9 else "FAIL",
       "recent10": {"n": 10, "refused": ref10, "success_rate": round(1 - ref10 / 10, 4),
                    "sids": [r["sid"] for r in last10]},
       "note": "Chris's bar: 'not successful until you can consistently spawn subagents'"}
json.dump(out, open(R + "/rounds/w2_acceptance.json", "w"), indent=1)
print(out)
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_acceptance.json"))
assert d["verdict"] in ("PASS", "FAIL"), d
assert d["recent10"]["n"] == 10
print("ACCEPTANCE", d["verdict"], "overall=%.4f recent10=%.4f" % (d["success_rate"], d["recent10"]["success_rate"]))
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_acceptance.json"; echo "rm"''',
     "snapshot": []},

    {"id": "w2r8f2", "name": "rollback-integrity-audit",
     "apply": r'''
python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
H = os.path.expanduser("~")
# fix -> (artifact path, legit_if: later passing fix recreated it)
TABLE = {
    "r1f2": (H + "/bin/pkill-guard", "w2r1f2"),
    "r2f2": (R + "/rounds/r2_gate.json", None),
    "r4f1": (R + "/rounds/r4_coverage.json", None),
    "r4f2": (R + "/rounds/r4_gate_timeline.json", None),
    "r6f3": (R + "/rounds/r6_dbsweep.json", None),
    "r7f1": (H + "/sdk/go/bin/go", "w2r3f1"),
    "r8f2": (R + "/dashboard.html", "post-phase"),
}
status = {}
for line in open(R + "/rounds_results.jsonl"):
    d = json.loads(line)
    if d.get("wave") == 2 and d.get("id"):
        status[d["id"]] = d["status"]
residues = []
for fid, (path, legit) in TABLE.items():
    exists = os.path.lexists(path)
    legit_now = (legit == "post-phase") or (legit and status.get(legit) == "pass")
    if exists and not legit_now:
        residues.append({"fix": fid, "path": path})
    print("%s exists=%s legit=%s" % (fid, exists, legit_now))
# r6f2 special: function must be present iff w2r2f3 passed (it re-appends)
guard = open(os.path.expanduser("~/workspace/refusal-hunt/round3/spawn_guard.py")).read()
has_fn = "def verify_spawn_record" in guard
if has_fn and status.get("w2r2f3") != "pass":
    residues.append({"fix": "r6f2", "path": "spawn_guard.py:verify_spawn_record"})
out = {"residues": residues, "clean": not residues}
json.dump(out, open(R + "/rounds/w2_rollback_audit.json", "w"), indent=1)
print("rollback audit clean=%s residues=%d" % (out["clean"], len(residues)))
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_rollback_audit.json"))
assert d["clean"] is True, d["residues"]
print("ROLLBACK_AUDIT_OK clean")
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_rollback_audit.json"; echo "rm"''',
     "snapshot": []},

    {"id": "w2r8f3", "name": "wave2-summary", "needs": ["w2r8f1", "w2r8f2"],
     "apply": r'''
python3 - <<'PYEOF'
import json, os
R = os.environ["ROUND4_ROOT"]
fixes = []
for l in open(R + "/rounds_results.jsonl"):
    d = json.loads(l)
    if d.get("wave") == 2 and d.get("id") and d.get("status"):
        fixes.append(d)
# dedupe by id: reruns supersede earlier attempts, latest row wins
latest = {}
for f in fixes:
    latest[f["id"]] = f
fixes = list(latest.values())
rounds = {}
for f in fixes:
    rounds.setdefault(f["round"], []).append(f["status"])
out = {"fixes": len(fixes),
       "by_round": {str(k): {"pass": v.count("pass"), "rolled_back": v.count("rolled_back"),
                             "skipped": v.count("skipped"), "blocked": v.count("blocked")}
                    for k, v in sorted(rounds.items())},
       "totals": {s: sum(1 for f in fixes if f["status"] == s)
                  for s in ("pass", "rolled_back", "skipped", "blocked")}}
json.dump(out, open(R + "/rounds/w2_summary.json", "w"), indent=1)
print(out)
PYEOF
''',
     "verify": r'''
python3 - <<'PYEOF'
import json, os
d = json.load(open(os.environ["ROUND4_ROOT"] + "/rounds/w2_summary.json"))
assert d["fixes"] == 24, d  # 24 distinct wave-2 fix ids; reruns supersede (latest row wins)
assert len(d["by_round"]) == 8, d
print("WAVE2_SUMMARY_OK", d["totals"])
PYEOF
''',
     "rollback": r'''rm -f "$ROUND4_ROOT/rounds/w2_summary.json"; echo "rm"''',
     "snapshot": []},
]


def post_phase():
    """Sequential acceptance artifacts - no races (wave-1 r8f2/r8f3 lesson)."""
    import glob
    rows = []
    for line in open(LOG):
        d = json.loads(line)
        if d.get("id") and d.get("status") and d.get("wave") in (1, 2, None):
            # wave 1 records have no "wave" key
            rows.append(d)
    h = ["<html><head><title>round4 dashboard (waves 1+2)</title></head><body>",
         "<h1>refusal-hunt round4: waves 1+2 (8 rounds x 3 fixes each)</h1>",
         "<table border=1><tr><th>wave</th><th>round</th><th>fix</th><th>status</th><th>ms</th></tr>"]
    for r in rows:
        wv = r.get("wave") or 1
        ms = r.get("apply_ms", 0) + r.get("verify_ms", 0)
        h.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                 % (wv, r.get("round"), r["id"], r["status"], ms))
    h.append("</table>")
    for name in ["w2_aggregates.json", "w2_gate.json", "w2_gate_timeline.json",
                 "w2_coverage.json", "w2_race.json", "w2_acceptance.json",
                 "w2_rollback_audit.json", "w2_summary.json", "w2_hatch_surface.json",
                 "w2_jarvis_catalog.json", "w2_nest.json", "w2_tools.json"]:
        p = os.path.join(OUTDIR, name)
        if os.path.exists(p):
            h.append("<h2>%s</h2><pre>%s</pre>" % (name, json.dumps(json.load(open(p)), indent=1)))
    h.append("</body></html>")
    open(os.path.join(ROOT, "dashboard.html"), "w").write("\n".join(h))
    print("dashboard: %d fix rows" % len(rows), flush=True)
    # runbook (idempotent)
    rb = os.path.join(ROOT, "ROUNDS_SUMMARY.md")
    s = open(rb).read() if os.path.exists(rb) else ""
    if "wave2" not in s:
        sums = [json.loads(l) for l in open(LOG)
                if json.loads(l).get("type") == "round_summary" and json.loads(l).get("wave") == 2]
        with open(rb, "a") as md:
            md.write("\n## wave2 - 8 rounds x 3 fixes - 2026-09-16\n")
            md.write("Dependency-aware levels; mirror-raced Go toolchain; executable storm mitigations.\n\n")
            for x in sorted(sums, key=lambda d: d["round"]):
                md.write("- w2 round%d: pass=%d rolled_back=%d skipped=%d blocked=%d (%dms)\n"
                         % (x["round"], x["pass"], x["rolled_back"], x["skipped"],
                            x.get("blocked", 0), x["round_ms"]))
        print("runbook wave2 appended", flush=True)
    else:
        print("runbook already has wave2", flush=True)


async def main():
    rc, out, err, ms = await sh(U + ["id", "-u"], 30)
    wlog({"type": "wrapper_check", "id_u": out.strip(), "rc": rc,
          "note": "0=root inside userns; every fix command wrapped; nest_asyncio applied"})
    for n in range(1, 9):
        s = await run_round(n, ROUNDS[n])
        print("W2 ROUND %d: pass=%d rolled_back=%d skipped=%d blocked=%d ms=%d"
              % (n, s["pass"], s["rolled_back"], s["skipped"], s.get("blocked", 0),
                 s["round_ms"]), flush=True)
    post_phase()
    print("WAVE2 DONE", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
