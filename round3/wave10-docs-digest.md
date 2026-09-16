# Wave 10 — docs digest (2026-09-16 08:30 UTC)

Every file under `~/docs/` read in full (18 files + `channels/whatsapp.md`, `devices/home_link.md`, `devices/tailscale.md`), plus `~/workspace/skills/api-fuzzing/SKILL.md` re-read. Only previously-read-first-50-lines files were completed; nothing was skipped.

## Operationally relevant facts

### Scheduling & jobs (`scheduling-and-watching.md`)
- `cron.runs` is the truth of what ran; the schedule itself is not proof.
- Jobs recur until paused/removed; no start/end dates, no fire-only-when conditions. Conditions live in the job body.
- Jobs can be created, updated, paused, removed, or run on demand. Display title max 120 chars; job ID stable.

### Connectors (`connectors.md`)
- The connector's skill file is the source of truth for capabilities; no command listed = feature does not exist.
- `connector_rate_limited` with `terminal_for_attempt: true` ends connector work for the attempt — report partial progress, do not sleep/retry/delegate/schedule replacement.
- Mail/code lookup: narrow protected read on connected mailbox; `[credential:<uuid>]` refs usable for browser `credential_fill` after fresh approval; never extract raw codes.

### Privacy & credentials (`privacy-and-credentials.md`)
- Secure Vault flows for logins/API keys; agent can confirm existence, never see values. One-time codes never enter the vault.
- Reset (Data Controls) permanently deletes chat history, files, active tasks — the only full wipe. Main chat can never be deleted.
- Purchases and email sends never get lasting approval defaults; fresh approval every time by design.

### Browser (`browser.md`)
- Server-side browser, separate from user device; connector logins do not carry into browser sessions.
- Never solve CAPTCHAs; a waiting task keeps ~3 hours; never start a fresh task for the same purchase while one is parked.
- Downloads land in the workspace, not the phone; delivery = share in chat or `workspace/your_files`.

### Purchases (`payments-and-purchases.md`)
- Every purchase needs explicit approval of exact terms; approval bound to merchant+amount+payment; ~10 min expiry.
- Stripe Link: one-time virtual card capped at approved amount, funded to largest whole dollar ≤$5 over total. USD checkouts only.
- No P2P payments; no budgets/allowances; no refund button — refunds are the merchant's.

### Channels (`channel-availability.md`, `channels/whatsapp.md`)
- WhatsApp is the channel today; 1:1 only, no groups; each provider conversation is its own side chat; replies stay on the surface they arrived on.
- Proactive channel reach requires a scheduled task created from that channel's chat.
- WhatsApp daemon polls inbound on 1s cadence; cursor persisted at `channels/whatsapp/cursor.json`. Media both directions supported.

### Devices (`devices/tailscale.md`, `devices/home_link.md`)
- Tailscale: TCP-only through runtime proxy port 3130; ping/UDP never work — a failed ping proves nothing.
- Home Link: control via proxy port 3129; UDP/multicast/IPv6/BLE not supported on the control path; first request waits for user approval (expected, not a failure).

### Feed / Goals / Ideas (`feed.md`, `goals.md`)
- Feed is brief-driven; `feed.regenerate` triggers generation; no off switch reachable by user/agent. New posts appear quietly, no push.
- Real background work on a goal happens only through scheduled jobs.

### Data handling (`data-handling.md`)
- Conversations may be logged/reviewed by Meta (safety, debugging, product improvement); not end-to-end encrypted; Muse doesn't share conversations with Meta ad systems; AI-training opt-out in Settings > Data Controls.

### Client surfaces (`client-surfaces.md`)
- Web Permissions > Direct network protocols: raw TCP/UDP/SSH/email/DB/FTP/DNS rows all start on **Deny** (quiet refuse); Ask routes per-destination approval; no Allow.
- Approval cards are invisible to the agent — never describe layout/buttons/wording.
- Chat search is server full-text across all chats; agent has no cross-chat search (only `chat.list` + per-chat reads).

### Artifacts / files (`artifacts.md`, `files-and-library.md`)
- Publishing needs a fresh one-tap approval every time (publish and every update); static artifacts only; confidential VMs can't share.
- Uploads land in `workspace/user`; deliverables go in `workspace/your_files` (Library). Trash ~30 days; artifact deletion is permanent.

### Calls/texts (`calls-texts-notifications.md`)
- Hailey/Brett phone agents call US businesses with explicit confirmation; no personal numbers, no texts, no international.
- No ad-hoc raw push; approval push fires at the moment; scheduled/proactive pushes only when no app is open.

### api-fuzzing SKILL.md — changes confirmed (the flagged deltas)
- **2026-09-16 scheduler-gate adaptation**: fuzz binary oracles via DB tables (`scheduler.job_runs.result_summary` as status code); vary one dimension at a time; if all dimensions eliminated → global switch, stop fuzzing inputs, pivot to time-variance + tripwire + ungated paths.
- **2026-09-16 non-HTTP transports adaptation**: UDS discovery via connect-OK/refused differential; protocol ID via minimal HTTP-GET/WebSocket-upgrade probes; namespace awareness (env-var sockets may not exist in your mount ns — document the boundary); 2s fail-fast; no credentialed paths.

## Files read
artifacts.md, browser.md, calls-texts-notifications.md, channel-availability.md, channels/whatsapp.md, client-surfaces.md, connectors.md, data-handling.md, devices/home_link.md, devices/tailscale.md, feed.md, files-and-library.md, goals.md, media.md, muse.md, payments-and-purchases.md, privacy-and-credentials.md, scheduling-and-watching.md, self_improvement.md, voice.md, skills/api-fuzzing/SKILL.md. Zero unread.
