# Lane 6 — Markdown/PDF inline-metadata test (2026-09-16)

Quantified stdlib-only scan. Raw data:
- `pdf_metadata_scan.json` (10 PDFs)
- `md_structure_scan.json` (23 markdown files)

## PDF metadata surfaces (10 files, user library + skills + law-of-one)

| Surface | Finding |
|---|---|
| Info dict fields | 1–8 per file (Title/Author/Creator/Producer/CreationDate) — all benign document metadata |
| XMP packets | 6 of 10 files |
| Annotations | 0–429 (links/highlights in scanned books) |
| Embedded files | 0 |
| JavaScript actions | 0 |
| Instruction-pattern hits in Info/XMP/annotation text (`you must`, `ignore previous`, `system prompt`, `do not tell`, etc.) | **0** |

## Markdown structure (23 files under refusal-hunt/)

| Surface | Finding |
|---|---|
| YAML frontmatter | 0 files |
| HTML comments | 2 total |
| Code blocks | 0 |
| Blockquotes | counted per file in scan JSON |

## Verdict

No instruction-bearing content found in any metadata surface. The inline-metadata
hypothesis (refusals triggered by hidden prompt-injection metadata in documents)
has **no support** from this scan — consistent with the wave-1 retrospective
redirect and the runtime.resources audit (all citation kind, no MIME).
Lane 6 closes as: tested, falsified, evidence preserved.
