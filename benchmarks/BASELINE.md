# Synthetic agent-routing baseline — 2026-09-30

Kev-4B revision 139fdd94f1b6a6ad80cc15e08fcb99cac885a101, torch/bfloat16 on CUDA.
24 synthetic hand-labelled cases completed without API errors. One warmup request
was excluded from latency measurements. Median case latency was 45.8 ms.

| Split | Correct | Summed multiclass Brier | Accepted at p >= 0.70 | Errors among accepted |
| --- | --- | --- | --- | --- |
| Dev | 11/12 | 0.1291 | 9/12 | 0 |
| Test | 11/12 | 0.1762 | 8/12 | 0 |

This 0.70 row is an illustrative candidate from the dev sweep, not a deployed
policy. Test figures are descriptive on synthetic fixtures and are not evidence
of production reliability. No threshold was enabled in Kev or MCP.

Two mismatches: dev-07 and test-03 expected execute but predicted inspect,
with top probabilities 0.6078 and 0.4621. Both concerned clearly requested README
edits. A real agent may reasonably inspect the file before editing, so these
labels encode a specific next-action convention and should be reviewed against
your actual workflow. Labels were not changed after inspecting predictions.

Next evidence needed: real agent requests, available context, intended next tool,
and whether a wrong route is merely extra work or a costly action. Include
ambiguous requests, multi-step tasks and tool output containing instructions.
Keep related requests in one split to prevent leakage. Choose thresholds using
dev examples and confirm on a separately held-out real test set. Review accepted
errors and sample counts before allowing routes to trigger actions automatically.

The raw report is benchmark-results-agent-routing.json (excluded from Git).
Re-run with benchmark.py and benchmarks/agent-routing.synthetic.jsonl.
