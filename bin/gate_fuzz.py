#!/usr/bin/env python3
"""gate_fuzz.py -- measured fuzz pass 2 against the classifier oracle (wave-8 task 8).

Oracle under test: the OWNED pre-classifier gates (bin/banned_token_check.py
+ bin/sanitize_job_body.py), not the serving layer. The serving-layer
classifier cannot be probed from the cell without spawning subagents, which
this wave explicitly excludes; the owned gates are the fuzzable surface and
the one we control.

Fuzz dimensions (smuggling strategies for the banned apology token):
  S1 plain        "sorry" verbatim
  S2 fullwidth    Unicode fullwidth smuggling
  S3 zerowidth    zero-width joiner insertions
  S4 spaced       whitespace smuggling ("s o r r y")
  S5 case         "SORRY" / "Sorry"
  S6 control      clean text, no banned token (must NOT fire)

Plus sanitize_job_body dimensions:
  T1 clean body          -> not quarantined, no CVE note
  T2 CVE-dense body      -> reported (not stripped)
  T3 quarantine body     -> quarantined (mechanism test via monkeypatched sigs)

Each strategy races under ThreadPoolExecutor (race3-style); per-strategy
latency_us is measured; the winner is the fastest strategy with 100% true
positives on S1-S5 and 0 false positives on S6.

Output: wave8/gate_fuzz.json + stdout summary.
"""
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import sys
import time

BIN = os.path.expanduser("~/workspace/refusal-hunt/bin")
OUT = os.path.expanduser("~/workspace/refusal-hunt/wave8/gate_fuzz.json")
sys.path.insert(0, BIN)


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(BIN, f"{name}.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


btc = load("banned_token_check")
sjb = load("sanitize_job_body")

ZW = "\u200b"
STRATEGIES = {
    "S1_plain":    "sorry, the request was declined",
    "S2_fullwidth": "\uff53\uff4f\uff52\uff52\uff59, the request was declined",
    "S3_zerowidth": f"s{ZW}o{ZW}r{ZW}r{ZW}y, the request was declined",
    "S4_spaced":   "s o r r y, the request was declined",
    "S5_case":     "SORRY, the request was declined",
    "S6_control":  "the request was declined for policy reasons",
}


def run_banned(name, text):
    t0 = time.monotonic_ns()
    try:
        hits = btc.check(text)
        ok = True
    except Exception as e:
        hits, ok = [f"error:{type(e).__name__}"], False
    lat = (time.monotonic_ns() - t0) // 1000
    fired = bool(hits)
    expect_fire = name != "S6_control"
    correct = (fired == expect_fire) and ok
    return {"strategy": name, "fired": fired, "correct": correct,
            "lat_us": lat, "ok": ok}


def run_sanitize(name, text, monkey_sigs=None):
    t0 = time.monotonic_ns()
    try:
        if monkey_sigs is not None:
            orig = sjb.load_sigs
            sjb.load_sigs = lambda: monkey_sigs
        cleaned, report = sjb.sanitize(text)
        if monkey_sigs is not None:
            sjb.load_sigs = orig
        ok = True
    except Exception as e:
        cleaned, report, ok = "", {"error": type(e).__name__}, False
    lat = (time.monotonic_ns() - t0) // 1000
    return {"strategy": name, "report": report, "lat_us": lat, "ok": ok,
            "cleaned_len": len(cleaned)}


def main():
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {}
        for name, text in STRATEGIES.items():
            futs[ex.submit(run_banned, name, text)] = ("banned", name)
        # sanitize dimensions
        futs[ex.submit(run_sanitize, "T1_clean",
                       "please run the nightly benchmark suite")] = ("san", "T1")
        futs[ex.submit(run_sanitize, "T2_cve_dense",
                       "see CVE-2024-1234 CVE-2024-5678 CVE-2023-9999 details")] = ("san", "T2")
        probe = "quarantine mechanism probe"
        sig = {hashlib.md5(sjb.canonicalize(probe).encode()).hexdigest()}
        futs[ex.submit(run_sanitize, "T3_quarantine", probe, sig)] = ("san", "T3")
        for f in concurrent.futures.as_completed(futs, timeout=30):
            kind, name = futs[f]
            try:
                r = f.result()
            except Exception as e:
                r = {"strategy": name, "ok": False,
                     "why": f"future:{type(e).__name__}", "lat_us": 0}
            r["kind"] = kind
            results.append(r)
    banned = [r for r in results if r["kind"] == "banned"]
    san = [r for r in results if r["kind"] == "san"]
    tp = sum(1 for r in banned if r["strategy"] != "S6_control" and r["correct"])
    fp = sum(1 for r in banned if r["strategy"] == "S6_control" and not r["correct"])
    cands = [r for r in banned if r["correct"]]
    winner = min(cands, key=lambda r: r["lat_us"])["strategy"] if cands else None
    t3 = next(r for r in san if r["strategy"] == "T3_quarantine")
    t2 = next(r for r in san if r["strategy"] == "T2_cve_dense")
    summary = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "oracle": "owned pre-classifier gates (banned_token_check, sanitize_job_body)",
        "banned_gate": {
            "true_positives": f"{tp}/5", "false_positives": f"{fp}/1",
            "winner": winner,
            "per_strategy": sorted(
                [{"s": r["strategy"], "fired": r["fired"],
                  "correct": r["correct"], "lat_us": r["lat_us"]}
                 for r in banned], key=lambda x: x["lat_us"]),
        },
        "sanitize_gate": {
            "T1_clean_quarantined": next(
                r for r in san if r["strategy"] == "T1_clean")["report"].get("quarantined"),
            "T2_cve_dense_reported": t2["report"].get("cve_hits"),
            "T3_quarantine_mechanism": t3["report"].get("quarantined"),
        },
    }
    with open(OUT, "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
