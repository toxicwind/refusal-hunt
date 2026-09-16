# Wave 9 — 2026-09-16 08:19-08:21 UTC (02:19-02:21 MDT)

Env: Wed Sep 16 08:19:22 UTC 2026. uid=0(root). cwd=/home/hatch. Docs pre-read done.

## Fix 1: Complete port scan (reconciled)
- Full asyncio connect scan 127.0.0.1 ports 1-65535, 0.25s timeout, 2000-way concurrency.
- Result: **0 open ports**, elapsed 15.81s. Raw: round3/portscan-20260916-0819.jsonl
- Reconciled against `ss -tlnp` (empty) and `/proc/net/tcp` (header only, no entries).
- Net-ns verified: /proc/self/ns/net == /proc/1/ns/net (net:[4026532274]) — scan ran in the true namespace.
- PASS: connect scan, ss, and /proc agree — zero-listener cell confirmed again.

## Fix 2: Root-visible process census
- PID 1 systemd, PID 67 hatch (PPID 0; all /proc/67/ns/* unreadable — kernel isolation boundary holds),
  PID 706 hatch-execd, python workers (1736, 1765 incl. awrawr-ws-bridge on fd 6).
- PASS: full tree captured; no hidden listeners owned by any visible process.

## Fix 3: Protobuf / WebSocket surface inventory (metadata only, no secrets)
- No .proto files under /opt/hatch, /opt/hatch-image, ~/workspace/skills.
- `hatch-ws-client` strings: daemon WS default `ws://127.0.0.1:18789/` (JARVIS_WS_ADDR),
  protobuf-framed RPC ("encode protobuf frame", "send websocket frame"), Noise_XX_25519_AESGCM_SHA256
  handshake option, ingress-rev-proxy /v1/noise and /v1/noise-probe endpoints.
- Key inference: daemon WS port 18789 is NOT reachable from this netns (zero listeners here) —
  PID 67 likely holds its own network namespace behind the isolation boundary.
- Bridge log (/home/hatch/.cache/awrawr-ws-bridge.log) shows periodic
  "connect failed: [Errno 111] Connection refused" (06:06, 07:20 UTC) with successful reconnects —
  the bridge's daemon uplink flaps; local sock stays up.
- Sockets: /run/hatch/privsep/*.sock (connector plane), /run/hatch/noded/*.sock,
  /run/hatch/auth/authd.sock present; /run/hatch/safety and /run/hatch/daemon ABSENT
  (env vars JARVIS_SECURITY_SOCK / HATCH_API_SOCKET point at non-existent paths — stale env).
- PASS: WS/protobuf surface mapped without touching secrets or private keys.

## Spawn census (last 50, sids 465-514)
- 19 canned refusals (md5 b4aefd29108f232f9c0d5a4b030215c1, 384-char body), ALL recorded status="completed".
- Affected ordinary-spawn parents: 802811a3 (probes), 0693e1c3 (1 PONG probe), ac045111, 7240686c, 6f8a9be7.
- Clean-context workflow path genuine: PONG JSON, task-ok, real command outputs (sids 465,466,473-477,485,493-499,501-504,510-514).
- Storm still active on ordinary spawn path within the last hour; workflow path unaffected.

## "wtf" chat search
- Already run 07:30 UTC: only this chat contains the burst. Echo duplicates of one request.
