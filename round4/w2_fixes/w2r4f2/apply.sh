#!/bin/bash
set -uo pipefail

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
