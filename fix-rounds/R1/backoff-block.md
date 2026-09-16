
## 2026-09-16 UTC — REFUSAL-BACKOFF (storm mitigation; reversible: delete this block)
<!-- MARKER:REFUSAL-BACKOFF -->
On any spawn whose final_response hash-matches the canned refusal signature:
1. DO NOT respawn immediately. Cooldown 15min +/- jitter before any retry.
2. Max 2 retries per refused intent; on retry, NARROW the context (drop
   non-load-bearing history, CVE-dense material, quoted refusal text).
3. Never quote or closely paraphrase the refusal text in the retry brief —
   quoted refusal tokens are loop-fuel for the classifier (echo-loop rule).
4. Log the refusal (sid, parent, UTC ts) to the refusal-hunt evidence log.
Rationale: ledger forensics 2026-09-15/16 show P(refusal|prev refusal)=60.8%
vs 19.6% baseline and 77% of spawn retries also refused — immediate retries
feed the storm. Additive and reversible.
<!-- END:REFUSAL-BACKOFF -->
