# R7b — Per-route timing and cost

## Spawn route segments, 24h (seconds)
- `genuine`: handoff median 0.0s (n=26), total median 2.0s p95 11.0s max 777.0s (n=26)
- `other:running`: handoff median 0.0s (n=1), total median Nones p95 Nones max Nones (n=0)
- `pending`: handoff median 0.0s (n=1), total median Nones p95 Nones max Nones (n=0)
- `refused_as_completed`: handoff median 0.0s (n=49), total median 2.0s p95 5.0s max 6.0s (n=53)

## Workflow route segments, 24h
- queue median 1.0s, exec median 1.0s (max 11.0s), statuses {'completed': 15, 'failed': 2, 'running': 1}
- tokens per child: median total 11987.5, max 308615.0 (v2 collector inherited full parent context)

## Cross-route read
- Refusals are FAST (~1s): serving-path reject, not a timeout or queue stall.
- Genuine spawn children and workflow children both execute in seconds; the workflow
  route's tax is context tokens, not latency.
- Inference-vs-execution: ledger records wall/model duration only; tool-execution split
  is not separately recorded in runtime.workflow_agent_calls.
