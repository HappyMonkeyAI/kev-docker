# Public benchmark pilot — 2026-09-30

Pinned Kev-4B 139fdd94f1b6a6ad80cc15e08fcb99cac885a101, torch/bfloat16 on an
RTX 5090 Laptop GPU. Evaluation used an isolated authenticated localhost container,
with existing model weights in offline mode. No tool action was executed by the
benchmark; the server only returned choice probabilities. No fine-tuning occurred.

| Adapted task | Correct | Accuracy | Median request latency | Mean Brier sum |
| --- | --- | --- | --- | --- |
| When2Call balanced sample | 287/400 | 71.75% | 121.5 ms | 0.4029 |
| ToolSelect valid rows | 534/552 | 96.74% | 54.1 ms | 0.0475 |

All 952 scored cases completed without API/response failures. Warmup requests are
excluded from latency. Latency is sequential end-to-end HTTP timing with caching,
not a throughput test. Converter/metric/export tests: 12 passed.

## When2Call findings

The fixed sample has 134 cannot_answer, 133 request_for_info and 133 tool_call
labels. All four proposed-response options are retained and reproducibly shuffled.
There are no correct-labelled direct answers in this source test set.

| Expected label | Correct in category | Predicted tool_call incorrectly |
| --- | --- | --- |
| cannot_answer | 83/134 | 34 |
| request_for_info | 90/133 | 30 |
| tool_call | 114/133 | n/a |

A descriptive p >= 0.80 cutoff accepts 125/400 cases, with five mistakes overall
and three inappropriate tool-call predictions. A p >= 0.90 cutoff accepts only
35/400 cases, with no observed mistakes. These are test-set descriptions, not
thresholds selected or validated for production. Cases derived from related
original requests may be correlated, so raw counts overstate independent evidence.

## ToolSelect findings

552 of 555 source rows were valid. Three labels/options could not be parsed or
matched and were excluded without repair; manifest.json lists row indices and
reasons. The Thought/Act answer section was excluded from inputs.
A descriptive p >= 0.80 cutoff accepts 495/552, with one mistake. This is an
upstream synthetic training corpus used exploratorily, not an official independent
held-out test and not evidence that the installed model never encountered it.

## Practical implication

These task-specific results suggest testing Kev as a tool-description matcher
first. Whether to call a tool, ask for missing information, or decline is a harder
and separate decision. Keep authorization, argument validation and dispatch in
the agent/controller; no automatic dispatch or threshold was enabled here.
The public tasks do not replace the private Hermes next-action evaluation.

When2Call already appears in Kev's published evaluations; the model card says it
was not a training source. Our adapted score should not be compared directly with
its published score because sample selection, prompts and option order differ.
https://github.com/jaredpalmer/kev/blob/main/docs/model-cards/kev-4b.md

Raw result reports: benchmark-results-when2call.json and
benchmark-results-toolselect.json in this directory (Git-ignored).
Source attribution, pinned revisions and transformations: README.md and manifest.json.
