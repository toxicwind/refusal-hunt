
## 8-round recursive fix run - 2026-09-16
Every command wrapped: unshare --user --map-root-user --mount (root in ns).

- round1: pass=2 rolled_back=1 skipped=0 (697ms)
- round2: pass=2 rolled_back=1 skipped=0 (231ms)
- round3: pass=3 rolled_back=0 skipped=0 (340ms)
- round4: pass=1 rolled_back=2 skipped=0 (260ms)
- round5: pass=3 rolled_back=0 skipped=0 (851ms)
- round6: pass=1 rolled_back=2 skipped=0 (482ms)
- round7: pass=0 rolled_back=1 skipped=2 (1965ms)

- round8: pass=1 rolled_back=2 skipped=0 (283ms)

Next iterations: live 6-spawn acceptance trial; gate-clear detector; feed autonomy blocked on DB reachability from supervisor (muse.db is operator-only).
