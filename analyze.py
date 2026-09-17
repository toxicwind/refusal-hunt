"""analyze.py: standard refusal-hunt analysis over the parquet debug state.
Usage: python3 analyze.py [--report DIR]
  - loads spawns.parquet, computes refusal stats, storm status, timing splits
  - every op timed at us resolution via utime
  - with --report DIR writes nightly report markdown into DIR
Refusal signature: md5(final_response) == b4aefd29108f232f9c0d5a4b030215c1 (stored as refused flag; never quote the string)
"""
import sys, os, datetime
import pandas as pd
from utime import span, log_event

HERE = os.path.dirname(os.path.abspath(__file__))
PARQUET = os.path.join(HERE, "spawns.parquet")

def load():
    with span("analyze.parquet_read", PARQUET):
        df = pd.read_parquet(PARQUET)
    df["dt"] = pd.to_datetime(df.created_at, unit="s", utc=True).dt.tz_convert("America/Denver")
    return df

def storm_status(df, now=None):
    now = now or pd.Timestamp.now(tz="America/Denver")
    out = {}
    for label, hours in (("6h", 6), ("24h", 24)):
        w = df[df.dt >= now - pd.Timedelta(hours=hours)]
        n = len(w); r = int(w.refused.sum())
        out[label] = {"n": n, "refused": r, "rate": round(r / n, 3) if n else 0.0}
    out["storm"] = out["6h"]["rate"] >= 0.5 and out["6h"]["n"] >= 3
    return out

def timing_split(df):
    with span("analyze.timing_split", f"rows={len(df)}"):
        ref = df[df.refused == 1].secs
        run = df[df.refused == 0].secs
        return {
            "refused": {"n": int(len(ref)), "min": float(ref.min()), "max": float(ref.max()),
                        "mean": round(float(ref.mean()), 2), "median": float(ref.median())},
            "ran": {"n": int(len(run)), "min": float(run.min()), "max": float(run.max()),
                    "mean": round(float(run.mean()), 2), "median": float(run.median())},
        }

def hourly_table(df, hours=48):
    with span("analyze.hourly", f"last {hours}h"):
        now = pd.Timestamp.now(tz="America/Denver")
        w = df[df.dt >= now - pd.Timedelta(hours=hours)].copy()
        w["hour"] = w.dt.dt.floor("h")
        h = w.groupby("hour").agg(n=("spawn_id", "size"), refused=("refused", "sum")).reset_index()
        h["rate"] = (h.refused / h.n).round(3)
        return h

def build_report(df):
    now = pd.Timestamp.now(tz="America/Denver").strftime("%Y-%m-%d %H:%M %Z")
    st = storm_status(df)
    ts = timing_split(df)
    h = hourly_table(df)
    lines = [f"# Refusal-hunt nightly report — {now}", "",
             f"Rows in debug state: {len(df)} (spawn_id {df.spawn_id.min()}–{df.spawn_id.max()})",
             f"Total refused (sig-hash): {int(df.refused.sum())} ({df.refused.mean():.1%})",
             f"Storm status: **{'STORM ON' if st['storm'] else 'clear'}** "
             f"(6h: {st['6h']['refused']}/{st['6h']['n']} refused, 24h: {st['24h']['refused']}/{st['24h']['n']})",
             "",
             "## Timing split (ledger seconds; us-level instrumentation in timings.parquet)",
             f"- refused: n={ts['refused']['n']} min={ts['refused']['min']}s max={ts['refused']['max']}s mean={ts['refused']['mean']}s",
             f"- ran: n={ts['ran']['n']} min={ts['ran']['min']}s median={ts['ran']['median']}s max={ts['ran']['max']}s",
             "",
             "## Hourly (last 48h)",
             "| hour | n | refused | rate |",
             "|---|---|---|---|"]
    for _, r in h.iterrows():
        lines.append(f"| {r['hour']} | {r.n} | {r.refused} | {r.rate} |")
    lines += ["",
              "Note: ledger `status` is a red herring — every refused row above is recorded `completed`. "
              "Verdict comes from the refusal hash + runtime + substance, never from status."]
    return "\n".join(lines)

def main():
    df = load()
    report_dir = None
    if "--report" in sys.argv:
        report_dir = sys.argv[sys.argv.index("--report") + 1]
    with span("analyze.build_report", ""):
        md = build_report(df)
    if report_dir:
        os.makedirs(report_dir, exist_ok=True)
        day = pd.Timestamp.now(tz="America/Denver").strftime("%Y-%m-%d")
        path = os.path.join(report_dir, f"{day}.md")
        with span("analyze.write_report", path):
            with open(path, "w") as f:
                f.write(md + "\n")
        print("wrote", path)
    else:
        print(md)
    st = storm_status(df)
    log_event("analyze.done", f"rows={len(df)} storm={st['storm']}")

if __name__ == "__main__":
    main()
