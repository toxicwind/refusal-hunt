# Wave 16 — transport-path expansion (2026-09-16 09:00 UTC)

## Binary scan (`/opt/hatch/bin/*`, strings)

- Three binaries reference `subagent_spawns`: `hatch`, `hatch-doctor`, `spawnd` (wave 12).
- `hatch` embeds a Rust noise-transport stack:
  - Crates: `hatch-engine/crates/noise-transport/src/dispatch/request.rs` (stream dispatch: `stream_id`, `method`, `status`, `bytes`, `termination`, `latency_ms`, priority fields), `hatch-engine/crates/ingress-rev-proxy/src/noise.rs`.
  - Protobuf wire validation: "payload is not canonical protobuf encoding", "Shared Agent payload exceeds 8192 bytes", "shared_agent_ticket must be a non-empty compact ASCII token", `N6google8protobuf14FatalExceptionE`.
  - Endpoints: `ws://127.0.0.1:18789`, `127.0.0.1:18792`, `ws://localhost`, `/v1/noise`, `/v1/noise-probe`, `/v1/noise-probe/ping`, `/run/hatch/daemon/http-api`.
  - Env: `JARVIS_WS_ADDR`, `JARVIS_AUTHD_SOCK`, `JARVIS_INFERENCE_PROXY_SOCK`, `JARVIS_STEFI_PROXY_SOCK`, `JARVIS_TELEMETRY_PROXY_SOCK`, `JARVIS_CREDIT_WATCHER_SOCK`, `JARVIS_HEALTHD_SOCKET`, `JARVIS_METRICS_SOCKET`, `JARVIS_RESCUE_SOCKET`, `JARVIS_SENTINEL_HTTP_API_SOCKET`.
- `spawnd` references `protobuf` (spawn ledger over a protobuf transport).
- No `.proto` files anywhere under `/opt/hatch`, `/opt/hatch-image`, or skills (confirmed wave 9).

## Bridge reconnect timeline (`~/.cache/awrawr-ws-bridge.log`, 86,893 lines; timestamps are UTC)

Target windows reconstructed exactly:
- **06:06:17 → 06:08:04 UTC: 107s outage.** Storm re-flare began ~06:32Z (26 min later).
- **07:20:15 → 07:20:48 UTC: 33s outage.** Chat burst 07:29–07:31Z (~9 min later).
- 08:26:23 → 08:27:19 UTC: 56s outage (during this wave block; post-dates the 08:22 spawn refusals).

Caveat: the bridge flaps constantly (dozens of reconnects/day: 16:55, 17:04, 17:49, 00:04, 00:35, 01:01, 01:07, 01:53, 01:56×2, 02:05, 03:04, 03:48×3, 04:00×2, 04:06, 04:18×2, 04:22×2, 05:17, 06:19, 07:50, 08:54, 09:54, 11:06, 14:55, 15:30, 15:58, 16:44×2, 17:19, 18:26, 19:18, 19:38, 20:39×2, 20:49, 21:54, 21:56×2, 21:57, plus the UTC-day entries). Temporal adjacency to storm windows is correlation against a high background flap rate — not evidence of causation. Typical reconnect completes in 2–35s; the 06:06 107s gap is the longest in the window.

## Interpretation
The daemon side speaks protobuf over a Noise-protocol WebSocket (`/v1/noise-probe`), defaulting to `127.0.0.1:18789` — but no listener exists in this namespace (wave 14), and PID 67's sockets are invisible across the boundary. The transport path is confirmed by binary strings only; live capture would require the daemon-side namespace. Nothing new contradicts the pre/post-classifier posture.
