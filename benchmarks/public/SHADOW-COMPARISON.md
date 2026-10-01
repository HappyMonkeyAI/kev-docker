# Paired shadow-helper comparison — 2026-09-30

All 552 valid pinned ToolSelect cases were evaluated through both the original
choice prompt and the actual kev_select_tool Python function. Requests used the
same model server, alternating baseline/shadow order per case, after one warmup
request per mode. No API or helper-validation failures occurred.

| Version | Correct | Accuracy | Median request latency |
| --- | --- | --- | --- |
| Original choice prompt | 534/552 | 96.74% | 42.9 ms |
| Actual shadow helper | 518/552 | 93.84% | 51.0 ms |

The helper lost 19 previously correct cases and fixed three previously incorrect
cases: a net loss of 16 cases, or 2.90 percentage points. It returned no tool on
21 cases whose source label names a supplied tool. Four of these false abstentions
had top probability at least 0.80. All four helper errors above that cutoff were
false abstentions in this run. No threshold was selected or deployed.

This comparison changes several things together: the helper prompt, description
rendering and an added __no_tool__ candidate in a fixed final position. It does not
isolate which change caused the difference. The added option can alter tool-choice
probabilities; original candidate order was held identical for each pair.

ToolSelect has no no-tool targets. Therefore this evaluates false abstentions,
not correct abstention recall. It remains an exploratory evaluation of a public
synthetic training corpus, with unresolved exposure/contamination limits and three
explicit source exclusions. These scores do not establish production reliability.
Do not compare latency across earlier runs as a controlled performance delta;
these medians are from this paired run and include caching/graph effects.

Keep the helper advisory. Before any trial influences agent decisions, evaluate
real cases with explicit available-tool schemas and independent labels, including
no-match and answer-without-tool cases. A comparison-only agent trial can collect
that evidence, but no Hermes configuration or running service was changed here.

Raw report: benchmark-results-shadow-paired.json (Git-ignored). It records case-level
pairs, dataset SHA-256, adapter-source SHA-256 and model metadata.
Runner: scripts/evaluate-shadow.py in kev-decision-mcp; it invokes the actual helper,
not a reimplementation. This assesses the Python helper path; MCP discovery was
verified previously, and transport overhead is not included in this comparison.
