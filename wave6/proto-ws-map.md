# Wave 6 — protobuf/WebSocket surface map (direct execution, 2026-09-16 ~07:15Z)

Subagent lane storm-refused; executed directly instead.

- No `.proto` files under `/opt/hatch` (bounded find, depth 5).
- No `ws://` or `wss://` URLs in `/opt/hatch` configs (*.json/*.yaml/*.toml).
- No `grpc.*` references in `/opt/hatch` JSON configs.
- Combined with the wave-5 binary-strings deobfuscation (`safety_client.rs`,
  `completion_gate.rs`, `review_kind` field): the agent is Rust, so any
  gRPC is tonic/prost with descriptors compiled into the binary, and no WS
  surface is declared in shipped configs.
- Queued: a second bounded byte-window pass over `/opt/hatch/bin/hatch`
  for transport/method-name symbols (wave-5 covered safety symbols).
