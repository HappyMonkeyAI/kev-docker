# Real-history pilot — 2026-09-30

Eight real Hermes requests were labelled by Codex after inspecting preceding
user/assistant messages, before observing model predictions. One candidate was
excluded because its model reference could not be resolved. Context was supplied
as reviewer summaries, not exact complete conversation replay. These labels are
provisional and have not been validated by the user or a second reviewer.

Kev-4B revision 139fdd94f1b6a6ad80cc15e08fcb99cac885a101 matched 5/8 labels
(62.5%). All API requests completed. Median measured case latency was 85.3 ms,
excluding warmup. This was sequential GPU inference with prefix caching enabled.

| Split | Label matches | Brier sum (mean) | Accepted at top probability >= 0.70 |
| --- | --- | --- | --- |
| Dev | 1/3 | 0.6723 | 1/3 |
| Test | 4/5 | 0.4419 | 0/5 |

The five-route policy includes respond, unlike the earlier four-route synthetic
baseline. These results cannot isolate whether the changed task distribution,
added route, context representation or label convention caused the difference.
A 0.70 cutoff would defer 7/8 requests. Lowering it based on this tiny pilot would
not establish a useful or reliable production policy. No policy was deployed.

Disagreements concerned save-to-file versus answer-only, inspect versus clarify
before environment setup, and research versus answer-only when earlier technical
advice conflicted. The inspect/clarify and research/respond cases may reasonably
need multiple actions; a single next-action label encodes a specific convention.
Do not interpret this pilot as an independent accuracy estimate of Kev.

Private requests, review notes, labels and raw results remain under
benchmarks/private/ and are excluded from Git. There are only three linked
session groups, and all concern one Kev deployment workflow. Exact duplicates
were grouped, but topical relatedness still limits split independence. No
clarify-labelled case remains in the reviewed set, and execute has one example.

Next useful changes: record structured agent state at the routing point (request,
relevant prior context, known targets, available tools and whether required facts
are verified), gather varied workflows, and validate labels. Compare route
suggestions in shadow mode before enabling automatic tool dispatch. Nothing in
this change modifies Hermes configuration or intercepts live agent requests.
