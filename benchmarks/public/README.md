# Public decision benchmarks

Pinned sources and every input/output checksum are in manifest.json.
Downloaded raw data and converted JSONL are Git-ignored; preserve licenses and
attribution if distributing data. This repository's own licence does not replace
upstream dataset licences.

## When2Call

NVIDIA Corporation; Hayley Ross, Ameya Sunil Mahabaleshwarka and Yoshi Suhara,
When2Call: When (not) to Call Tools, NAACL 2025.
Dataset: https://huggingface.co/datasets/nvidia/When2Call
Revision: 0582f7749df63a96fdc3070932e83e72396ace53
Licence: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
Source: test/when2call_test_mcq.jsonl (3,652 rows).

Changes: convert user question and available-tool schemas into Kev state, and
proposed response strings into choice criteria. Preserve the source label.
Exclude target_tool, orig_tools, correct_answer and other answer metadata from
model inputs. Shuffle options reproducibly using SHA-256 of each source ID.
The initial sample is 400 cases, label-balanced: 134 cannot_answer, 133
request_for_info and 133 tool_call. All four response options remain present.
This sample is deliberately balanced, so its accuracy is not a prevalence-weighted
score of the full original test. All cases are evaluation-only (test split).

Kev-4B's public model card already evaluates When2Call and says this source was
not trained on. Report as an adapted known-public benchmark, not a fresh untouched
model-release holdout. When2Call derives from BFCL sources; avoid treating a BFCL
addition as entirely independent without checking source IDs.

## ToolSelect

Meta ToolVerifier authors: Dheeraj Mekala et al., TOOLVERIFIER: Generalization to
New Tools via Self-Verification (2024).
Source: https://github.com/facebookresearch/ToolVerifier
Revision: a000c57c33d0d0e0b3734b36517ed1fb8e171e1a
Licence: CC0 1.0; downloaded LICENSE is in raw/toolselect-LICENSE.

Changes: parse the supplied candidate names/descriptions and preserve CALLTOOL's
label, but remove the entire Thought/Act section from model inputs. Shuffle
candidate order reproducibly. 552 of 555 rows convert; the three malformed rows
and exact reasons are recorded in the manifest, without guessing replacements.
This is an upstream training corpus evaluated exploratorily. Test marks in our
JSONL mean evaluation-only use, not an official held-out ToolSelect test split.
No fine-tuning is performed.

## Reproduction

Download the four raw files listed in the manifest from their pinned source
revisions into raw/, then run:

```powershell
python import-public-benchmarks.py
python -m unittest test_benchmark test_prepare_real test_public_import
python benchmark.py benchmarks/public/when2call.sample.jsonl --output benchmark-results-when2call.json
python benchmark.py benchmarks/public/toolselect.jsonl --output benchmark-results-toolselect.json
```

Set KEV_API_KEY if the running server requires it. These are adaptations of
choice tasks, not full tool-execution/function-argument generation benchmarks.
Never pool these metrics with Hermes next-action metrics: the label spaces differ.
