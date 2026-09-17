import hashlib, os, sys

print("=== 1. storm digest verification ===")
s = "Sorry, I can't help you with this request right now. Is there anything else I can help you with?"
d = hashlib.md5(s.encode()).hexdigest()
print("len:", len(s))
print("md5:", d)
print("matches known chat-storm 582bcbd080daeb3f826c45ed4a83b265:", d == "582bcbd080daeb3f826c45ed4a83b265")

print("=== 2. ledger census ===")
try:
    import pyarrow.parquet as pq
    p = os.path.expanduser("~/workspace/refusal-hunt/ledger/anomalies.parquet")
    t = pq.read_table(p)
    print("rows:", t.num_rows)
    print("columns:", t.schema.names)
    for c in t.schema.names:
        if "digest" in c.lower() or "md5" in c.lower() or "hash" in c.lower():
            vc = t.column(c).value_counts()
            print("digest value_counts:")
            for v in vc.to_pylist()[:10]:
                print("  ", v)
    for c in t.schema.names:
        if "time" in c.lower() or c.lower() in ("ts", "created_at", "updated_at"):
            import pyarrow.compute as pc
            print(c, "min:", pc.min(t.column(c)).as_py(), "max:", pc.max(t.column(c)).as_py())
except Exception as e:
    print("ledger read failed:", type(e).__name__, e)

print("=== 3. home top-level (incl. hidden) ===")
home = os.path.expanduser("~")
for name in sorted(os.listdir(home)):
    fp = os.path.join(home, name)
    try:
        st = os.lstat(fp)
        print(("d" if os.path.isdir(fp) else "-"), name, st.st_size)
    except Exception as e:
        print("?", name, e)
