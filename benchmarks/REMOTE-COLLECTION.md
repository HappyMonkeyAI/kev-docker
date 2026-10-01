# Remote Hermes collection — 2026-09-30

Key-based SSH access succeeded for the authorised Hermes host. The read-only Hermes
inventory found 441 sessions and 158,487 message records. Subagent sessions were
excluded from candidate extraction. The bounded scan covered up to 215 CLI sessions.

The private candidate file benchmarks/private/hermes-215.review.jsonl contains
81 unique requests from 58 session groups: 69 assigned dev and 12 test. Observed
first-call hints include 30 inspect, 16 execute, 5 clarify and 30 unclassified.
No research hints were retained by this scan; collection is not representative
of all tools or tasks. At most 30 candidates per hint are retained.

Known generated compaction and standing-goal/task-list messages were filtered.
CLI source and filtering still do not prove human authorship. Review remaining
records for automation/delegation wrappers before assigning labels. First tool
calls are behavior observations, not necessarily correct decisions.

Candidates include a preceding assistant excerpt, capped at 4,000 characters,
for review only. Excerpts are not automatically included in model state. Restore
relevant context under state before approval, note truncation, and keep related
sessions/workflows in one split. Exact user-request duplicates are removed;
near duplicates and shared project context still require reviewer judgement.

Collection ran over SSH with Python supplied on stdin, SQLite opened read-only,
and output saved locally. No script, configuration or dataset was written to the
remote host. Tool arguments, tool outputs and system prompts were not exported.
Redaction is best effort; personal content remains private and Git-ignored.
All candidates remain pending with no ground-truth claims or automatic routing.

A second candidate host was not accessed because its SSH host key was absent from the local
trusted known-hosts configuration. Existing trust checks were kept enabled.
