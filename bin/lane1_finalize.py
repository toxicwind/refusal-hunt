#!/usr/bin/env python3
"""Finalize lane1.json with applied-then-starts verdict."""
import json

p = "/home/hatch/workspace/refusal-hunt/storm-lanes/lane1.json"
d = json.load(open(p))
d["applied_then_starts_test"] = {
    "hypothesis": "storm onsets follow an applied event (cron add/update, job deploy) within 60 min",
    "verdict": "REJECTED",
    "onset_correlations": [
        {"onset": "2026-09-15T10:45:00+00:00", "n": 1,
         "applied_60min_before": "none (nearest: sidechat-watch adds 06:35Z, 4h before)"},
        {"onset": "2026-09-15T19:35:00+00:00", "n": 1,
         "applied_60min_before": "none (nearest: sidechat-watch adds 06:35Z, 13h before)"},
        {"onset": "2026-09-16T00:00:00+00:00", "n": 1,
         "applied_60min_before": "none"},
        {"onset": "2026-09-16T02:55:00+00:00", "n": 7,
         "applied_60min_before": "NONE - zero cron_mutations, zero job adds in prior 60 min; only routine scheduled watchdogs (sidechat-watch-*, squawk-ws-client-watchdog, service-restart-watchdog, whatsapp-fleet-digest), all status=succeeded"},
        {"onset": "2026-09-16T07:10:00+00:00", "n": 5,
         "applied_60min_before": "16 jobs ADDED 06:20:40-06:26:49Z (gate-x-p1-sysbody, gate-x-p2-nodelivery, gate-x-p3-goalowned, gate-x-p4-verbose, gate-x-l1..l6, doctor-followup, system-maintenance-probe, deterministic-doctor-2, fleet-snapshot-5m-2, gate-fuzz-control-1, squawk-ws-client-watchdog-2) - BUT spawn refusals predated additions (lane2 window opens 03:01Z < 06:20Z); correlation real, causation reversed"},
    ],
    "response_events_after_onset": [
        {"at": "2026-09-16T03:47Z",
         "what": "6 sidechat-watch jobs UPDATED + gate-probe-minimal ADDED",
         "relation_to_onset4": "52 min AFTER onset - incident response, not cause"},
    ],
    "corrected_causal_direction": "storm -> applied (diagnostic/response jobs follow onsets), NOT applied -> storm",
    "note": "The remembered feature-unlock ordering is backwards: the gate-x probe ladder was applied AFTER the storm started (02:55Z onset precedes 06:20Z adds), as a diagnostic response.",
}
d["confidence_0_100"] = {
    "time_series": 95,
    "onset_detection": 85,
    "applied_rejection": 90,
    "causal_reversal": 85,
}
json.dump(d, open(p, "w"), indent=2)
print("lane1.json finalized:", d["n_onsets"], "onsets, verdict:", d["applied_then_starts_test"]["verdict"])
