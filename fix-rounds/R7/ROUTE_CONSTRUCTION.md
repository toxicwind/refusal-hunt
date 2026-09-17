# R7a — Route-construction truth map

All three routes (main/root chat, subagent.spawn, workflow agent()) use model
`ipnext/avocado-5.16-v4` with uniformly null request metadata: agent_type, request_origin,
transcript_surface, root_work_class are NULL on every observed row. Construction fields do
NOT discriminate refused from genuine spawns — the census is identical on both sides.

## Refusal rate by requester_source (7d, 448 spawns)
- `runtime`: 59/430 refused (rate 0.1372, genuine 358, pending 1, other 12)
- `runtime.workflow`: 0/18 refused (rate 0.0, genuine 17, pending 0, other 1)

## Top refusing parents (7d)
- `7240686c`: 19/185 refused (rate 0.1027)
- `ff521137`: 19/25 refused (rate 0.76)
- `0783c1d6`: 9/13 refused (rate 0.6923)
- `f99a2d06`: 4/56 refused (rate 0.0714)
- `58246538`: 4/57 refused (rate 0.0702)
- `67fcb771`: 1/11 refused (rate 0.0909)
- `ac045111`: 1/1 refused (rate 1.0)
- `6f8a9be7`: 1/19 refused (rate 0.0526)
- `0693e1c3`: 1/1 refused (rate 1.0)
- `a0907f6c`: 0/2 refused (rate 0.0)

## Workflow route (24h, 18 calls)
- statuses: completed: 15, failed: 2, running: 1
- spawn-ledger rows with requester_source=runtime.workflow: 18, refused among them: 0
- the first v2verify collector (previously 'running') completed; all workflow children genuine.

## Conclusion
Route construction fields are IDENTICAL for refused and genuine spawns (no differing field). The discriminator is requester_source: the normal subagent.spawn path (runtime) carries the refusals while the workflow daemon path (runtime.workflow) has zero refusals on the same model. Refusal is a property of the serving path, not of any recorded parameter or content.
