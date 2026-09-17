"""Direct lane work after 8/8 spawn refusals. Section A: classify the refusal variant
by digest/length ONLY (never print bodies). Section B: Lane-1 storm timing census."""
import hashlib, json, glob, os
import pyarrow.parquet as pq
import pyarrow.compute as pc

OUT = os.path.expanduser("~/workspace/refusal-hunt/lanes/lane1-storm-timing")
os.makedirs(OUT, exist_ok=True)

print("=== A. refusal variant classification ===")
sess_files = glob.glob("/home/hatch/agents/agent-01753ecf-33bc-4ea2-a160-b081c19b6652/sessions/*.jsonl")
print("session files:", sess_files)
KNOWN = {"582bcbd080daeb3f826c45ed4a83b265": "chat-storm-96",
         "b4aefd29108f232f9c0d5a4b030215c1": "spawn-storm-384"}
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
seen = {}
for fp in sess_files:
    try:
        with open(fp) as f:
            lines = f.readlines()
    except Exception as e:
        print("read fail", fp, e); continue
    for ln in lines[-300:]:
        ln = ln.strip()
        if not ln: continue
        try: obj = json.loads(ln)
        except Exception: continue
        stack = [obj]
        while stack:
            o = stack.pop()
            if isinstance(o, dict):
                stack.extend(o.values())
            elif isinstance(o, list):
                stack.extend(o)
            elif isinstance(o, str) and len(o) > 120:
                h = md5(o)
                if h not in seen:
                    seen[h] = len(o)
for h, ln_ in sorted(seen.items(), key=lambda x: -x[1])[:12]:
    print(f"len={ln_} md5={h} known={KNOWN.get(h, 'NOVEL')}")

print("=== B. lane-1 storm timing census ===")
t = pq.read_table(os.path.expanduser("~/workspace/refusal-hunt/ledger/anomalies.parquet"))
print("rows:", t.num_rows, "| cols:", t.schema.names)
# session key: prefer parent_agent_id, fall back to child
import pyarrow as pa
df = t.to_pandas()
df["created_at"] = __import__("pandas").to_datetime(df["created_at"], format="mixed", utc=True)
df["sess"] = df["parent_agent_id"].fillna(df["child_agent_id"]).fillna(df["source"] + ":" + df["id"])
onsets = df.sort_values("created_at").groupby("sess").first().reset_index()
print("distinct sessions with storm rows:", len(onsets))
print("onset digest mix:", onsets["body_md5"].value_counts().to_dict())
# bursts: >=5 rows within any rolling 10-min window, per session
df = df.sort_values(["sess", "created_at"]).reset_index(drop=True)
df["prev5_ts"] = df.groupby("sess")["created_at"].shift(4)
df["span5"] = (df["created_at"] - df["prev5_ts"]).dt.total_seconds()
bursts = df[df["span5"] <= 600].copy()
print("rows inside burst windows (>=5 in 10min):", len(bursts), f"({100*len(bursts)/len(df):.1f}% of all storm rows)")
print("sessions with >=1 burst:", bursts["sess"].nunique())
# inter-arrival within sessions
df["delta_s"] = df.groupby("sess")["created_at"].diff().dt.total_seconds()
d = df["delta_s"].dropna()
print("inter-arrival median s:", d.median(), "| p90:", d.quantile(0.9), "| share <60s:", (d < 60).mean())
# hourly distribution of onsets (UTC)
onsets["hour"] = onsets["created_at"].dt.hour
print("onset hour histogram (UTC):", onsets["hour"].value_counts().sort_index().to_dict())
# persist
onsets_out = onsets[["sess", "created_at", "body_md5", "body_len"]].rename(columns={"created_at": "onset_ts"})
pq.write_table(pa.Table.from_pandas(onsets_out, preserve_index=False), os.path.join(OUT, "storm_onsets.parquet"), compression="zstd")
bout = bursts[["sess", "created_at", "body_md5", "span5"]].copy()
pq.write_table(pa.Table.from_pandas(bout, preserve_index=False), os.path.join(OUT, "bursts.parquet"), compression="zstd")
print("wrote:", OUT)
