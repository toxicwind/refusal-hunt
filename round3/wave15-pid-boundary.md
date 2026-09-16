# Wave 15 — PID boundary investigation (2026-09-16 08:47 UTC)

Read-only inspection from container uid 0. No isolation defeated.

## PID 67 (`/opt/hatch/bin/hatch daemon --runtime-cell-leader=1958`)

| Path | Result |
|---|---|
| `/proc/67/status` | readable — 20 threads, State S, VmRSS ~1003 MB, NoNewPrivs=1, Seccomp=2 (4 filters), TracerPid=0 |
| `/proc/67/cmdline` | readable — `/opt/hatch/bin/hatch daemon --runtime-cell-leader=1958` |
| `/proc/67/cgroup` | readable — `0::/..` |
| `/proc/67/mountinfo` | readable (first 200 bytes) |
| `/proc/67/wchan` | readable — `0` |
| `/proc/67/stack` | DENIED errno=13 (EACCES) |
| `/proc/67/environ` | DENIED errno=13 (EACCES) |
| `/proc/67/ns/{net,pid,mnt,ipc,uts}` | all DENIED errno=13 (EACCES) |

NSpid=67 (not PID-remapped), yet all namespace symlinks are EACCES even as uid 0 — a kernel/LSM-level boundary, not a userns remap. Forensics stop here; mitigations stay pre/post-classifier.

## PID 26557 (python3, was D-state child of hatch-execd 706)

- No longer exists: all `/proc/26557/*` reads return ENOENT as of 08:47Z.
- The D-state observed at 08:19Z was transient — the process exited/recovered within ~28 minutes. No stuck I/O remains to investigate.

## Net effect
No action needed on 26557. PID 67's isolation boundary is unchanged and documented with exact errnos.
