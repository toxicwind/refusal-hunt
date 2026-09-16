#!/usr/bin/env bash
# fix-r6c-orchestrator-race.sh — R6c: race orchestration strategies for the fix-round fan-out.
# Strategies: asyncio.gather (current driver) vs ThreadPool vs ProcessPool vs precompiled C
# fanout binary (built here with gcc) + GNU parallel remote-leg bonus on awrawr-pc.
# Also surveys pip for async alternatives (anyio/trio/uvloop).
# Snapshot: driver.py untouched by this fix (record-only). Rollback: rm binary/src/results.
set -u
R=~/workspace/refusal-hunt/fix-rounds/R6
BIN=~/workspace/bin/fanout
SRC=$R/fanout.c
RACE=$R/race-results.json
WIN=$R/orchestrator-winner.json

snapshot() { :; }  # driver.py not modified; nothing to snapshot

build_fanout() {
  cat > "$SRC" <<'CEOF'
/* fanout: precompiled parallel command orchestrator.
   usage: fanout <timeout_s> <cmd1> [cmd2 ...] — each cmd via sh -c, concurrent.
   prints "leg=i rc=N ms=M cmd=..." per leg; exit 0 iff all legs rc==0. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <sys/time.h>
#include <sys/wait.h>
static long long ms_now(void){
  struct timeval tv; gettimeofday(&tv,0);
  return (long long)tv.tv_sec*1000LL + tv.tv_usec/1000;
}
int main(int argc, char** argv){
  if(argc < 4){ fprintf(stderr,"usage: fanout <timeout_s> <cmd1> [cmd2 ...]\n"); return 2; }
  int n = argc - 2;
  long long timeout_ms = atoll(argv[1]) * 1000LL;
  pid_t* pids = calloc(n, sizeof(pid_t));
  long long* t0 = calloc(n, sizeof(long long));
  int* rc = malloc(n * sizeof(int));
  long long* dt = malloc(n * sizeof(long long));
  for(int i=0;i<n;i++){ rc[i]=-99; dt[i]=-1; }
  long long start = ms_now();
  for(int i=0;i<n;i++){
    t0[i] = ms_now();
    pid_t p = fork();
    if(p==0){ execl("/bin/sh","sh","-c",argv[2+i],(char*)0); _exit(127); }
    if(p<0){ rc[i]=126; dt[i]=0; } else pids[i]=p;
  }
  int left = n;
  for(int i=0;i<n;i++) if(rc[i]!=-99) left--;
  while(left > 0){
    long long now = ms_now();
    int timed_out = (now - start > timeout_ms);
    if(timed_out) for(int i=0;i<n;i++) if(rc[i]==-99 && pids[i]>0) kill(pids[i], SIGKILL);
    for(int i=0;i<n;i++){
      if(rc[i]!=-99 || pids[i]<=0) continue;
      int st; pid_t w = waitpid(pids[i], &st, WNOHANG);
      if(w==pids[i]){ rc[i]=WIFEXITED(st)?WEXITSTATUS(st):128; dt[i]=ms_now()-t0[i]; left--; }
      else if(w==-1 && errno==ECHILD){ rc[i]=125; dt[i]=ms_now()-t0[i]; left--; }
    }
    if(left>0) usleep(5000);
    if(ms_now() - start > timeout_ms + 8000) break;
  }
  int bad=0;
  for(int i=0;i<n;i++){
    if(rc[i]==-99){ rc[i]=124; dt[i]=ms_now()-t0[i]; }
    if(rc[i]!=0) bad++;
    printf("leg=%d rc=%d ms=%lld cmd=%.60s\n", i, rc[i], dt[i], argv[2+i]);
  }
  fflush(stdout);
  free(pids); free(t0); free(rc); free(dt);
  return bad?1:0;
}
CEOF
  gcc -O2 -Wall -o "$BIN" "$SRC" || return 1
  test -x "$BIN" || return 1
  "$BIN" 5 "true" "true" "true" | grep -q "rc=0" || return 1
  echo "fanout binary built: $BIN"
}

survey_packages() {
  echo "--- async package survey ---"
  python3 -c "import nest_asyncio; print('nest_asyncio: installed (driver hard-requires it)')" 2>&1
  for p in anyio trio uvloop; do
    timeout 25 pip index versions "$p" 2>&1 | grep -m1 -i "available versions" || echo "$p: pip index unavailable"
  done
  echo "--- precompiled/binary orchestration survey ---"
  ~/workspace/bin/br 'parallel --version 2>/dev/null | head -1; go version 2>/dev/null' 2>&1 | head -4 || echo "bridge survey unavailable"
}

race() {
  local leg=$R/leg.sh
  cat > "$leg" <<'LEOF'
#!/usr/bin/env bash
# synthetic fix-shaped leg: snapshot file, hash it 300x (cpu), verify, cleanup
f=$(mktemp /tmp/raceleg.XXXXXX) || exit 2
echo payload > "$f"
for i in $(seq 1 300); do sha256sum "$f" >/dev/null || exit 3; done
echo ok > "$f"; test "$(cat "$f")" = ok; rc=$?
rm -f "$f"; exit $rc
LEOF
  chmod +x "$leg"
  python3 - "$leg" "$RACE" <<'PYEOF'
import asyncio, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
leg, racep = sys.argv[1], sys.argv[2]
def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True).returncode
t0=time.monotonic()
async def amain():
    async def one():
        p = await asyncio.create_subprocess_shell(leg, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await p.communicate(); return p.returncode
    return await asyncio.gather(one(), one(), one())
r_asyncio = asyncio.run(amain()); d_asyncio = time.monotonic()-t0
t0=time.monotonic()
with ThreadPoolExecutor(3) as ex: r_threads = list(ex.map(lambda _: run(leg), range(3)))
d_threads = time.monotonic()-t0
t0=time.monotonic()
with ProcessPoolExecutor(3) as ex: r_procs = list(ex.map(run, [leg]*3))
d_procs = time.monotonic()-t0
t0=time.monotonic()
binp = os.path.expanduser("~/workspace/bin/fanout")
p = subprocess.run([binp, "120", leg, leg, leg], capture_output=True, text=True)
d_fanout = time.monotonic()-t0
res = {
  "asyncio":   {"secs": round(d_asyncio,3), "ok": all(r==0 for r in r_asyncio)},
  "threads":   {"secs": round(d_threads,3), "ok": all(r==0 for r in r_threads)},
  "processes": {"secs": round(d_procs,3),   "ok": all(r==0 for r in r_procs)},
  "fanout":    {"secs": round(d_fanout,3),  "ok": p.returncode==0, "legs": p.stdout.strip().splitlines()},
}
json.dump(res, open(racep, "w"), indent=1)
cands = {k: v["secs"] for k, v in res.items() if v["ok"]}
winner = min(cands, key=cands.get) if cands else None
json.dump({"winner": winner, "margin_vs_asyncio": round(res["asyncio"]["secs"]-cands[winner],3) if winner else None,
           "all": res, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
          open(os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R6/orchestrator-winner.json"), "w"), indent=1)
print("winner:", winner, {k: v["secs"] for k, v in res.items()})
PYEOF
}

gnu_parallel_bonus() {
  echo "--- GNU parallel remote-leg bonus (awrawr-pc) ---"
  ~/workspace/bin/br 't0=$(date +%s%N); parallel -j3 --tagstring leg-{} "echo {}" ::: a b c 2>&1 | head -5; t1=$(date +%s%N); echo "parallel_3legs_ms=$(( (t1-t0)/1000000 ))"' 2>&1 | head -8 || true
}

apply() { build_fanout && survey_packages && race && gnu_parallel_bonus; }

verify() {
  test -x "$BIN" || return 1
  python3 - "$WIN" "$RACE" <<'PYEOF'
import json, sys
w = json.load(open(sys.argv[1])); r = json.load(open(sys.argv[2]))
assert w["winner"] in ("asyncio","threads","processes","fanout"), w["winner"]
assert all(v["ok"] for v in r.values()), "all strategies must pass all legs"
print("race valid: winner=%s margin_vs_asyncio=%ss, all 4 strategies 3/3 legs ok" % (w["winner"], w["margin_vs_asyncio"]))
PYEOF
}

rollback() { rm -f "$BIN" "$SRC" "$RACE" "$WIN" "$R/leg.sh"; }

case "${1:-run}" in
  run) snapshot && apply && verify && echo "R6c PASS" ;;
  rollback) rollback ;;
esac
