# P1.2 post-remote recovery zero-progress diagnostic — 2026-09-08

Status: LIVE DIAGNOSTIC CHECKPOINT

The bounded same-thread recovery attempt had already timed out after 300 seconds with `ROLLOUT_COMPACT_MARKERS_PRE_RECOVERY=5`.

A read-only safe parser was then run against the private `post-remote-recovery.jsonl` trace. It reported:

- private thread recovered: yes
- partial same thread: yes
- partial agent message count: 0
- partial completed command count: 0
- partial file change count: 0
- partial MCP call count: 0
- partial error item count: 0
- partial HTTP 403 classification: no
- partial transport-error classification: no
- result file exists: no
- result exact: no

Interpretation:

The latest 300-second timeout occurred before any agent message or completed client tool call was observed. It is therefore distinct from the earlier duplicate-workspace-guard failure, which had already been repaired and covered by CI.

Because the same rollout had accumulated five compaction markers before this attempt, the next diagnostic is intentionally read-only: compare the rollout's current compaction marker count with the previously observed value of 5. If the count increased during the zero-progress attempt, repeated pre-turn auto/remote compaction is the leading blocker. If it did not increase, investigation should move to the pre-first-response continuation/browser path rather than compaction.

No private thread identifier, prompt body, synthetic token, local command body, browser/account data, or private trace content is recorded here.
