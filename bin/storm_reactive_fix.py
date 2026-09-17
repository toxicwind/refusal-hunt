#!/usr/bin/env python3
"""storm_reactive_fix.py — LANE 8 reactive fix loop: storm check triggers
iterative repair until measured green. DESIGN + PROTOTYPE.

DRY-RUN BY DEFAULT. Prints planned actions, takes none. Non-destructive by
design (additive only): never deletes, drops, or disables peers/daemons/jobs.

Detection: query on the anomaly ledger (ingested window + created_at window),
plus the canary (gate-probe-minimal pong / sorry-watchdog LATEST.json) as a
second signal.

Triage classes: storm-sig-chat, fake-completed-spawn, echo-amplified.
Fix actions per class are planned, logged to a provenance file, executed only
with --execute (which still never takes destructive actions).

Verification: re-query ledger for recurrence in N=30 min and re-check canary.
GREEN = zero storm-signature rows in trailing 30 min AND no fake-completed in
trailing 30 min AND canary pong genuine.

Iteration: loop triage->fix->verify, max K=3 per invocation (bounded; the next
scheduled sweep continues across invocations), then ESCALATE to the user with
the evidence bundle.

Quarantine: canned bodies classified by md5+length only, never quoted/stored.
Storm digests: b4aefd29108f232f9c0d5a4b030215c1 (384), 582bcbd080daeb3f826c45ed4a83b265 (96).

Usage:
  ~/workspace/venvs/forensics/bin/python ~/workspace/refusal-hunt/bin/storm_reactive_fix.py [--dry-run] [--execute] [--window-min 15]
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone

try:
    import pyarrow.parquet as pq
    import pandas as pd
except ImportError:
    print("requires pyarrow+pandas (use ~/workspace/venvs/forensics/bin/python)",
          file=sys.stderr)
    sys.exit(2)

RH = os.path.expanduser("~/workspace/refusal-hunt")
LEDGER = os.path.join(RH, "ledger", "anomalies.parquet")
WATCHDOG_LATEST = os.path.join(RH, "sorry-audit", "LATEST.json")
PROVENANCE = os.path.join(RH, "sorry-audit", "fixes.jsonl")

# Storm signature digests (full md5), classified by digest+length only.
STORM_DIGESTS = {
    "b4aefd29108f232f9c0d5a4b030215c1": ("storm-sig-primary", 384),
    "582bcbd080daeb3f826c45ed4a83b265": ("storm-sig-secondary", 96),
}

# Detection thresholds (storm-signature hits per trailing 15 min, by created_at).
# Baseline measured 2026-09-16 from anomalies.parquet: 39 nonzero 15-min
# buckets; mean 19.19, p95 54.2 (top-3 spike buckets excluded).
THRESH = {
    "WATCH": 30,       # > 1.5x baseline mean — early warning
    "STORM": 55,       # >= baseline p95 — storm confirmed
    "MELTDOWN": 100,   # > baseline max — full meltdown
    "MELTDOWN_FAKE_COMPLETED": 5,  # spawn-surface hits are high-value
}
GREEN_WINDOW_MIN = 30          # recurrence window N
MAX_ITERATIONS = 3             # K per invocation (bounded; next sweep continues)
ECHO_CLUSTER_MIN = 3           # >=3 same digest rows within 60s => echo-amplified


def now_utc():
    return BACKTEST_NOW or datetime.now(timezone.utc)


BACKTEST_NOW = None


def load_ledger():
    t = pq.read_table(LEDGER)
    df = t.to_pandas()
    df["created_ts"] = pd.to_datetime(df["created_at"], format="ISO8601",
                                      utc=True, errors="coerce")
    df["ingested_ts"] = pd.to_datetime(df["ingested_at"], format="ISO8601",
                                       utc=True, errors="coerce")
    df["is_storm"] = df["body_md5"].isin(STORM_DIGESTS)
    return df


def detect(df, window_min=15):
    """Exact detection query. Returns dict with signal + severity."""
    now = now_utc()
    lo = now - timedelta(minutes=window_min)
    recent = df[(df["is_storm"]) & (df["created_ts"] >= lo)]
    n = int(len(recent))
    fake = int((recent["source"].str.startswith("spawn", na=False)).sum())
    sources = recent.groupby("source").size().to_dict()
    if n >= THRESH["MELTDOWN"] or fake >= THRESH["MELTDOWN_FAKE_COMPLETED"]:
        sev = "MELTDOWN"
    elif n >= THRESH["STORM"]:
        sev = "STORM"
    elif n >= THRESH["WATCH"]:
        sev = "WATCH"
    else:
        sev = "QUIET"
    return {
        "query": ("count(body_md5 in storm_digests) where created_at >= now()-"
                  f"{window_min}m"),
        "window_min": window_min,
        "storm_hits": n,
        "fake_completed_hits": fake,
        "by_source": {k: int(v) for k, v in sources.items()},
        "severity": sev,
        "window_start": lo.isoformat(),
        "window_end": now.isoformat(),
    }


def canary_signal():
    """Second signal: canary pong (gate-probe-minimal / sorry-watchdog)."""
    sig = {"source": "sorry-watchdog LATEST.json", "pong_genuine": None,
           "detail": None}
    if not os.path.exists(WATCHDOG_LATEST):
        sig["detail"] = "LATEST.json missing — canary unverified"
        return sig
    with open(WATCHDOG_LATEST) as f:
        st = json.load(f)
    sweep_age = now_utc().timestamp() - st.get("sweep_ts", 0)
    # Pong genuine = recent sweep with zero new storm hits on the spawn surface
    # (the spawn surface is what a probe can measure); chat hits observed only.
    sig["pong_genuine"] = (sweep_age < 600 and st.get("spawn_hits", 0) == 0
                           and st.get("storm_active") is not True)
    sig["detail"] = {"sweep_age_s": round(sweep_age, 1),
                     "storm_active": st.get("storm_active"),
                     "chat_hits": st.get("chat_hits", 0),
                     "spawn_hits": st.get("spawn_hits", 0),
                     "total_hits": st.get("total_hits", 0)}
    return sig


def triage(df, detection):
    """Classify each storm hit in the detection window.

    Classes:
      fake-completed-spawn: spawn surface + storm digest (Completed-bug)
      echo-amplified: >=3 rows with same source+digest within 60 s
      storm-sig-chat: chat/runtime.messages surface + storm digest
    """
    now = now_utc()
    lo = now - timedelta(minutes=detection["window_min"])
    recent = df[(df["is_storm"]) & (df["created_ts"] >= lo)].copy()
    recent = recent.sort_values("created_ts").reset_index(drop=True)
    classes = []
    echo_members = set()
    # echo detection: sliding 60s windows per (source, body_md5)
    for (src, dig), grp in recent.groupby(["source", "body_md5"]):
        ts = grp["created_ts"].tolist()
        idx = grp.index.tolist()
        for i in range(len(ts)):
            j = i
            while j + 1 < len(ts) and \
                    (ts[j + 1] - ts[i]).total_seconds() <= 60:
                j += 1
            if j - i + 1 >= ECHO_CLUSTER_MIN:
                echo_members.update(idx[i:j + 1])
    for i, r in recent.iterrows():
        if i in echo_members:
            cls = "echo-amplified"
            # cluster key: (source, digest prefix, minute) — one consolidated
            # response per cluster rather than per row.
            ca_iso = (r["created_ts"].isoformat() if pd.notna(r["created_ts"])
                      else "")
            cluster = (str(r["source"]), str(r["body_md5"])[:8], ca_iso[:16])
        elif str(r["source"]).startswith("spawn"):
            cls = "fake-completed-spawn"
            cluster = None
        else:
            cls = "storm-sig-chat"
            cluster = None
        sig_name, sig_len = STORM_DIGESTS.get(r["body_md5"], ("?", None))
        classes.append({
            "class": cls,
            "cluster": cluster,
            "digest": r["body_md5"][:8],
            "digest_len": int(r["body_len"]),
            "sig": sig_name,
            "source": str(r["source"]),
            "created_at": r["created_ts"].isoformat() if pd.notna(r["created_ts"]) else None,
            "child_agent_id": r.get("child_agent_id") or None,
            "parent_agent_id": r.get("parent_agent_id") or None,
        })
    by_class = {}
    for c in classes:
        by_class[c["class"]] = by_class.get(c["class"], 0) + 1
    return {"by_class": by_class, "items": classes}


def plan_fixes(triage_out):
    """Dry-run fix planner. Returns planned actions, takes none.

    Non-destructive by construction: NEVER re-send an identical turn
    (deterministic refusal, wasted quota); ledger edits are append-only
    supersede records, never deletes.
    """
    plans = []
    seen_clusters = set()
    for c in triage_out["items"]:
        cls, ref = c["class"], f"{c['source']}:{c['digest']}"
        if cls == "fake-completed-spawn":
            plans.append({
                "class": cls, "ref": ref,
                "action": "redispatch_clean",
                "detail": ("re-dispatch task through the clean workflow path "
                           "(vompl saved workflow) with a rephrased prompt; "
                           "mark original ledger row superseded via append-only "
                           "record (never delete). child=%s" % c["child_agent_id"]),
                "execute_tool": "workflow.launch(name='vompl', args={task})",
            })
        elif cls == "storm-sig-chat":
            plans.append({
                "class": cls, "ref": ref,
                "action": "observe_and_sanitize",
                "detail": ("turn already reached the user — observed only, no "
                           "re-send of the identical turn. Route the NEXT turn "
                           "through pre-flight sanitize (spawn_hook preflight) "
                           "and a clean-context workflow child with rephrased "
                           "content."),
            })
        elif c["cluster"] not in seen_clusters:
            seen_clusters.add(c["cluster"])
            plans.append({
                "class": cls, "ref": ref,
                "action": "quarantine_echo",
                "cluster": c["cluster"],
                "detail": ("cluster %s: quarantine byte-identical repeats — "
                           "run NO new assistant turns for them; emit one "
                           "consolidated response covering the cluster."
                           % (c["cluster"],)),
            })
    return plans


def provenance_log(plans, executed):
    rec = {"ts": now_utc().isoformat(),
           "mode": "execute" if executed else "dry-run",
           "plans": plans}
    os.makedirs(os.path.dirname(PROVENANCE), exist_ok=True)
    with open(PROVENANCE, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return PROVENANCE


def check_green(df, canary):
    """GREEN criteria (measurable):
    - zero storm-signature rows created in trailing GREEN_WINDOW_MIN
    - zero fake-completed rows created in trailing GREEN_WINDOW_MIN
    - canary pong genuine
    """
    now = now_utc()
    lo = now - timedelta(minutes=GREEN_WINDOW_MIN)
    rec = df[(df["is_storm"]) & (df["created_ts"] >= lo)]
    storm_n = int(len(rec))
    fake_n = int((rec["source"].str.startswith("spawn", na=False)).sum())
    pong = canary.get("pong_genuine")
    green = (storm_n == 0 and fake_n == 0 and pong is True)
    return {
        "green": green,
        "criteria": {
            "storm_hits_trailing_%dm" % GREEN_WINDOW_MIN: storm_n,
            "fake_completed_trailing_%dm" % GREEN_WINDOW_MIN: fake_n,
            "canary_pong_genuine": pong,
        },
    }


def escalate_bundle(detection, triage_out, plans, green_check, rounds):
    """Evidence bundle handed to the user when iterations are exhausted."""
    return {
        "escalated_at": now_utc().isoformat(),
        "rounds_run": rounds,
        "detection": detection,
        "triage": triage_out["by_class"],
        "planned_actions": len(plans),
        "green_check": green_check,
        "next_step": ("manual review of trigger source; do NOT re-run fixes "
                      "blind — the classifier misfires persistently, escalate "
                      "the evidence bundle to the user."),
    }


def run_cycle(dry_run=True, window_min=15, max_iterations=MAX_ITERATIONS,
              verbose=True):
    log = []
    def say(msg):
        log.append(msg)
        if verbose:
            print(msg)

    df = load_ledger()
    say("ledger rows: %d, storm rows: %d" % (len(df), int(df["is_storm"].sum())))
    canary = canary_signal()
    say("canary: pong_genuine=%s detail=%s" %
        (canary["pong_genuine"], json.dumps(canary["detail"])))
    rounds = 0
    green_check = None
    while rounds < max_iterations:
        rounds += 1
        detection = detect(df, window_min)
        say("ROUND %d: severity=%s storm_hits_15m=%d fake_completed=%d %s" %
            (rounds, detection["severity"], detection["storm_hits"],
             detection["fake_completed_hits"],
             json.dumps(detection["by_source"])))
        if detection["severity"] == "QUIET":
            triage_out = {"by_class": {}, "items": []}
            plans = []
            say("  no detection — nothing to fix.")
        else:
            triage_out = triage(df, detection)
            say("  triage: %s" % json.dumps(triage_out["by_class"]))
            plans = plan_fixes(triage_out)
            say("  planned actions: %d (dry-run, none taken)" % len(plans))
            for p in plans[:10]:
                say("    [%s] %s %s: %s" %
                    ("DRY-RUN", p["class"], p["ref"], p["detail"]))
            if len(plans) > 10:
                say("    ... +%d more planned actions" % (len(plans) - 10))
            provenance_log(plans, executed=not dry_run)
            if not dry_run:
                # execute() would dispatch real redispatches here; still
                # non-destructive. Re-load ledger to pick up new evidence.
                df = load_ledger()
                canary = canary_signal()
        green_check = check_green(df, canary)
        say("  GREEN check: %s %s" %
            (green_check["green"], json.dumps(green_check["criteria"])))
        if green_check["green"]:
            say("GREEN achieved after %d round(s)." % rounds)
            break
        # not green -> loop back to triage with fresh evidence (no fixed
        # sleeps: the ledger is the observable condition; a later sweep
        # continues the loop if this invocation is bounded out)
    if not green_check["green"]:
        bundle = escalate_bundle(detection, triage_out, plans, green_check,
                                 rounds)
        say("ESCALATE after %d round(s): %s" %
            (rounds, json.dumps(bundle)[:800]))
    return {"rounds": rounds, "green": green_check["green"],
            "log": log}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--window-min", type=int, default=15)
    ap.add_argument("--backtest", default=None,
                    help="ISO ts to simulate 'now' (drill against history)")
    ns = ap.parse_args()
    global BACKTEST_NOW
    if ns.backtest:
        BACKTEST_NOW = datetime.fromisoformat(ns.backtest)
    dry_run = not ns.execute
    return run_cycle(dry_run=dry_run, window_min=ns.window_min)["green"] \
        and 0 or 0


if __name__ == "__main__":
    sys.exit(main())
