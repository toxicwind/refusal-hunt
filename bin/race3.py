#!/usr/bin/env python3
"""fail-fast racer: N strategies, per-attempt ceiling (default 3s), nested
fallback chains. First VALID result wins. Losers are data, not failures.
Usage: race3.py --timeout 3 --json strategies.json   (strategies: [{name, cmd[], match?}])
"""
import json, subprocess, sys, time, concurrent.futures

def run_one(s, timeout):
    t0 = time.monotonic_ns()
    try:
        try:
            p = subprocess.run(s["cmd"], capture_output=True, text=True, timeout=timeout)
            ok = p.returncode == 0
            out = (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            return {"name": s["name"], "ok": False, "why": "timeout", "lat_us": (time.monotonic_ns()-t0)//1000}
        except FileNotFoundError:
            return {"name": s["name"], "ok": False, "why": "no-binary", "lat_us": (time.monotonic_ns()-t0)//1000}
        except Exception as e:  # nested fallback: never let one strategy kill the race
            return {"name": s["name"], "ok": False, "why": f"error:{type(e).__name__}", "lat_us": (time.monotonic_ns()-t0)//1000}
        lat_us = (time.monotonic_ns()-t0)//1000
        if ok and s.get("match") and s["match"] not in out:
            return {"name": s["name"], "ok": False, "why": "match-miss", "lat_us": lat_us}
        return {"name": s["name"], "ok": ok, "why": "" if ok else "nonzero-exit", "lat_us": lat_us,
                "out": out[:400] if ok else out[:200]}
    except Exception as e:
        return {"name": s["name"], "ok": False, "why": f"outer:{type(e).__name__}", "lat_us": (time.monotonic_ns()-t0)//1000}

def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--timeout", type=float, default=3.0)
    ap.add_argument("--json", required=True); a = ap.parse_args()
    strat = json.load(open(a.json))["strategies"]
    results, winner = [], None
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(strat)) as ex:
        futs = {ex.submit(run_one, s, a.timeout): s["name"] for s in strat}
        try:
            for f in concurrent.futures.as_completed(futs, timeout=a.timeout + 2):
                try:
                    r = f.result()
                except Exception as e:
                    r = {"name": futs[f], "ok": False, "why": f"future:{type(e).__name__}", "lat_us": 0}
                results.append(r)
                if r["ok"] and winner is None:
                    winner = r["name"]
                    break
        except concurrent.futures.TimeoutError:
            pass
    for f in futs:  # fail fast: don't await losers
        f.cancel()
    print(json.dumps({"winner": winner, "attempts": sorted(results, key=lambda r: r["lat_us"])}))

if __name__ == "__main__":
    main()
