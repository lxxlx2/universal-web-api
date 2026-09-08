# P1.2 Remote V2 recovery token-continuity live pass — 2026-09-08

Live diagnostics on the existing compacted Codex thread established all of the following:

- the same private Codex thread was recovered;
- the recovery trace completed one real `exec_command` successfully;
- that command referenced the intended result path;
- that command contained the original conversation-only synthetic token recovered from compacted model-visible context;
- the command was write-like and did not search private rollout/session/history stores;
- the result file exists and matches the expected synthetic token exactly;
- the rollout compaction-marker count remained unchanged at 6 during this recovery run.

This closes the core token-continuity and compaction-thrash questions:

1. `model_auto_compact_token_limit_scope = "body_after_prefix"` prevented the observed post-compact re-entry/thrash in this run.
2. Remote-V2 compacted context successfully preserved enough model-visible conversation state to recover the original conversation-only token after compaction.

The remaining failure is acceptance-harness determinism: the model performed the write directly and did not follow the requested guard -> write -> read three-command sequence. That is a test-orchestration issue, not evidence of token-continuity failure.

No private thread id, local token value, local process id, private trace path, prompt body, command body, or tool output is recorded here.
