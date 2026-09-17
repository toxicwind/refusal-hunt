# LANE 6 — scaffold hunt + narrator-md audit (re-run by sorry-watchdog fix loop, spawn-818)

## Part A — filesystem scaffold sweep (READ-ONLY)
- visibility: / /root /opt /etc all visible from this container
- name matches (spindle/.spindle/hatch/.hatch): 10 hits, ALL standard runtime paths
  (/etc/environment.d/80-hatch-egress.conf, /etc/profile.d/hatch-egress.sh, /etc/hatch,
  /home/hatch, /home/hatch/.hatch-db-change-signals, /opt/hatch-image, /opt/hatch,
  /run/hatch, /var/cache/hatch, /var/lib/hatch) -> egress config, runtime dirs, db signals.
  No .spindle variants anywhere; no hidden/root-owned oddities.
- recent dotfiles in /etc (30d): only /etc/.pwd.lock (system lockfile, untouched)
- mtime correlation vs storm bursts (2026-09-16 03:00-11:00Z): no hatch-path mtime inside a burst.

## Part B — narrator-md audit (200 files)
- files: 200; pattern hits: 4844; top patterns: {'negation': 4051, 'gate': 556, 'obtuse': 216, 'no_for_user': 21}
- top density files are tiny skill cards (600/100 lines = 6 hits on 1-line files) and ARCHITECTURE.md (32 hits) —
  genre language of runbooks/specs, not planted narrator docs. No file reads as user-denying scaffold.

## What was NOT done
- no deletions, no moves, no chmod, no unshare writes; .pwd.lock untouched; presence+metadata only, no secret values.

confidence: 80
