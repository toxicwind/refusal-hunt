# LANE 5 — client echo + composite replay [WIP — 2026-09-17 correction: echo is INTENTIONAL]

> WIP. Prior framing treated echo as a bug/amplifier to dedupe. Corrected 2026-09-17 per Chris: echo is purposeful — re-sending to punch through the storm to the actual model. DO NOT DEDUPE. Do not build echo-collapse/dedupe watermarks.

- byte-identical user-message groups (top 20, last 3d): sizes 27x..417x; median avg inter-arrival 4s
- largest group: single-char message (md5 5058f1af) replayed 417x across the window — intentional tap/retry echo, not a bug
- 2x/3x/5x+ distribution: every top-20 group is >=17x; long tail of smaller groups exists below the top-40 cut
- replay-vs-storm contingency (storm row within +-60s of group span): 17/20 groups overlap a storm row
- composite-replay candidates (>800 chars, prefix+verbatim-copy pattern): 8 in top 20 (e.g. 1830/7573/6774/2673/1774-char groups at 24x-56x)
- headline: intentional echo — the same user message re-sends a median of ~40x within minutes (top-group medians);
  most storm rows sit inside echo bursts, consistent with the punch-through model: classifier fires, intentional re-send pushes through to the actual model.
- % of storm rows preceded by a re-send within 60s: approximated by group overlap = 85%

confidence: 70 (group-by-md5 aggregates are exact; 120s-bounded windows approximated by group spans)

## timings (ms)
- storm_join: 73
- persist: 14
