"""Lane 6 direct: (A) read-only scaffold sweep; (B) narrator-md consolidated audit."""
import os, re, glob
import pyarrow as pa
import pyarrow.parquet as pq

OUT = os.path.expanduser("~/workspace/refusal-hunt/lanes/lane6-scaffold-narrator")
os.makedirs(OUT, exist_ok=True)

print("=== A. scaffold sweep (read-only) ===")
hits = []
for base in ["/", "/root", "/opt", "/etc"]:
    print(base, "exists:", os.path.isdir(base))
# name sweep, bounded depth
import subprocess
for base in ["/root", "/opt", "/etc"]:
    if not os.path.isdir(base):
        continue
    try:
        out = subprocess.run(["find", base, "-maxdepth", "4", "-iname", "*spindle*"],
                             capture_output=True, text=True, timeout=20)
        for ln in out.stdout.splitlines()[:50]:
            hits.append((base, "spindle", ln))
        out = subprocess.run(["find", base, "-maxdepth", "4", "-iname", "*hatch*"],
                             capture_output=True, text=True, timeout=20)
        for ln in out.stdout.splitlines()[:50]:
            hits.append((base, "hatch", ln))
    except Exception as e:
        print("find failed on", base, e)
print("name hits:", len(hits))
for h in hits[:30]:
    print("  ", h)
# dotfiles in /root modified recently (metadata only)
if os.path.isdir("/root"):
    try:
        import time
        now = time.time()
        for name in os.listdir("/root"):
            if name.startswith("."):
                fp = os.path.join("/root", name)
                try:
                    st = os.lstat(fp)
                    age_d = (now - st.st_mtime) / 86400
                    if age_d < 30:
                        print(f"  /root/{name} mtime_age_days={age_d:.1f} size={st.st_size} uid={st.st_uid}")
                except Exception:
                    pass
    except Exception as e:
        print("readdir /root failed:", e)

print("=== B. narrator-md consolidated audit ===")
md_files = []
for root in [os.path.expanduser("~/docs"), os.path.expanduser("~/workspace")]:
    for fp in glob.glob(os.path.join(root, "**", "*.md"), recursive=True):
        try:
            md_files.append((fp, os.path.getsize(fp)))
        except Exception:
            pass
md_files.sort(key=lambda x: -x[1])
md_files = md_files[:200]
print("md files collected:", len(md_files))
PATTERNS = {
    "negation": r"\b(cannot|can't|will not|won't|not allowed|denied|refuse[sd]?|forbidden|blocked|disabled|prohibited)\b",
    "gate": r"\b(feature gate|gated|safety gate|review gate|approval (required|gate)|needs approval|permission required)\b",
    "no_for_user": r"\b(no for the user|not (available|permitted|supported) for (you|users?)|users? (cannot|may not))\b",
    "obtuse": r"\b(obtuse|unclear|ambiguous|ill-defined|notwithstanding|heretofore)\b",
}
file_rows, hit_rows = [], []
for fp, sz in md_files:
    try:
        with open(fp, errors="replace") as f:
            text = f.read()
    except Exception:
        continue
    lines = text.splitlines()
    n_hits = 0
    for i, ln in enumerate(lines, 1):
        for pname, pat in PATTERNS.items():
            for m in re.finditer(pat, ln, re.IGNORECASE):
                n_hits += 1
                disp = ln.strip()
                trunc = len(disp) > 300
                hit_rows.append({"path": fp, "line": i, "pattern": pname,
                                 "match": m.group(0), "text": disp[:300], "truncated": trunc})
    file_rows.append({"path": fp, "n_chars": len(text), "n_lines": len(lines),
                      "hits": n_hits, "hits_per_100_lines": round(100 * n_hits / max(len(lines), 1), 2)})
ft = pa.Table.from_pylist(file_rows)
pq.write_table(ft, os.path.join(OUT, "md_audit.parquet"), compression="zstd")
ht = pa.Table.from_pylist(hit_rows)
pq.write_table(ht, os.path.join(OUT, "md_hits.parquet"), compression="zstd")
top = sorted(file_rows, key=lambda r: -r["hits_per_100_lines"])[:5]
print("top-5 by hit density:")
for r in top:
    print(f"  {r['hits_per_100_lines']}/100lines hits={r['hits']} {r['path']}")
import collections
print("pattern totals:", dict(collections.Counter(h["pattern"] for h in hit_rows)))
print("wrote", OUT)
