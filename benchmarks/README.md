# Agent-routing benchmark

agent-routing.synthetic.jsonl contains 24 hand-labelled synthetic fixtures,
12 dev and 12 test. Labels implement the policy embedded in each question.
They are bootstrap examples, not real agent traffic or an independent production
evaluation. Review ambiguous labels before reusing the policy.

Each JSONL row has id, split (dev/test), state, questions, and expected.
Choice labels name a criterion; noul labels are booleans; score labels are integer
criterion indices. Every question must have a target. Use unique case IDs.
Store private labelled traffic under benchmarks/private/ (excluded from Git).
Do not reuse this synthetic split to justify a production threshold.

Run benchmark.py DATASET --url http://127.0.0.1:8008 --output benchmark-results.json.
Set KEV_API_KEY in the client environment when authentication is enabled.
The output records model metadata, a dataset checksum, per-question results,
accuracy, summed multiclass Brier score, calibration bins and threshold coverage.
Score questions also report expected-score MAE. Thresholds use top probability,
not the model confidence field. An explicit clarify prediction is a route;
probability-based deferral is separate and should fall back to an agent/human.

Choose candidate thresholds on dev examples, then confirm them on independent,
real test examples. Accepted accuracy with very few accepted examples is weak
evidence; inspect counts and costly failures. No threshold is selected automatically.
Repeated-state prefix caching can affect latency; this is a quality benchmark,
not a controlled throughput test. Failed cases are listed and return a nonzero
exit status; reported metrics exclude them and are incomplete until resolved.

## Real Hermes requests

prepare-real-benchmark.py reads the local Hermes SQLite database in read-only mode.
It exports user requests and first observed tool names, omitting tool arguments,
outputs and system prompts. Redaction is best effort: inspect private records
before sharing them. Nine unique candidates were extracted from four sessions
on 2026-09-30 into benchmarks/private/agent-routing.review.jsonl.

Observed tool names are hints, not ground-truth labels. All candidates start pending.
Restore necessary context under state, choose expected_route, set context_complete
and privacy_reviewed to true, and set review_status to approved only after review.
Exact repeated requests link session groups; duplicates are removed. Keep related
workflows together when extending the dataset. Hashes are identifiers, not anonymisation.

Real traffic adds a fifth route, respond, for answers needing no tool. The earlier
four-route synthetic baseline does not evaluate this expanded routing policy.

Export approved labels with:

```powershell
python prepare-real-benchmark.py export-reviewed benchmarks/private/agent-routing.review.jsonl
python benchmark.py benchmarks/private/agent-routing.labelled.jsonl
```

The export rejects missing context/privacy review, duplicate states and a session
appearing in both splits. This tiny sample is not enough to set production thresholds.

Eight candidates now have provisional Codex-reviewed labels and one is excluded.
See REAL-PILOT.md for the first scored real-history pilot and its limitations.
