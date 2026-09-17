# Wave 14 — full network census (2026-09-16 08:40 UTC)

Script: `~/workspace/refusal-hunt/round3/wave14-census.py` → `wave14-net-census.jsonl`.

## Results

| Surface | Count |
|---|---|
| TCP LISTEN (IPv4, all local addrs) | 0 |
| TCP LISTEN (IPv6) | 0 |
| UDP sockets (IPv4) | 0 |
| UDP sockets (IPv6) | 0 |
| Unix sockets | 350 |
| Net namespace: PID 1 vs self | identical (`net:[4026532274]`) |

`ss -tlnp` / `ss -ulnp` agree: no TCP or UDP listeners. No banner probes were needed — nothing to probe.

## Unix-socket → PID reconciliation

- 350 unix sockets enumerated; only 18 inodes map to PIDs visible in this PID namespace.
- `/home/hatch/.cache/awrawr-ws-bridge.sock` → PID 1765 (visible, the bridge).
- All `/run/hatch/*` service sockets (`auth/authd.sock`, `safety/security.sock`, `cron-store/control.sock`, `exec/execd.sock`, `noded/*`, `sandbox/*`, `sandbox-api/api.sock`, `proxy/inference.sock`, `proxy/stefi.sock`, `telemetry/telemetry.sock`, `whatsapp-keyd/keyd.sock`, `credit-watcher/credit-watcher.sock`, `postgres/.s.PGSQL.5432`) → **no visible owning PID**.
- New vs wave 9: `safety/security.sock`, `cron-store/control.sock`, `exec/execd.sock`, `proxy/inference.sock`, `proxy/stefi.sock`, `telemetry/telemetry.sock`, `whatsapp-keyd/keyd.sock`, `credit-watcher/credit-watcher.sock`, `postgres/.s.PGSQL.5432` enumerated this round.

## Interpretation

Zero-listener cell confirmed for the third time (waves 7, 9, 14): no TCP/UDP service exists in this network namespace. The runtime's service sockets are all bound by processes in a PID namespace invisible from here — consistent with the PID 67 kernel-isolation boundary. Review/classifier enforcement has no in-container network surface; forensics stop at the namespace boundary.
