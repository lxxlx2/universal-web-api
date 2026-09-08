# P1.2 Remote V2 post-compaction recovery — CLOSED — 2026-09-08

P1.2 is closed on composite live + CI evidence.

## Live evidence

The acceptance sequence proved:

- native Codex remote-V2 compaction triggered through UWA;
- the same private Codex thread was resumed after compaction;
- the original conversation-only synthetic token was recovered from model-visible compacted context without searching private Codex/UWA history stores;
- a real local `exec_command` wrote the recovered token to the acceptance result path;
- the result file matched the expected token exactly;
- after switching UWA mode to Codex's supported `model_auto_compact_token_limit_scope = "body_after_prefix"`, the recovery run completed without another compaction marker being added;
- the earlier post-compact compaction-thrash behavior therefore did not recur in the decisive run.

## Required-tool / orchestration hardening

During debugging, two independent harness/protocol issues were found and fixed:

1. explicit Chinese required-tool wording that the parser did not previously recognize;
2. duplicate required-tool enforcement on continuation after a matching `function_call` + `function_call_output` had already satisfied the latest user turn.

Both fixes are covered by regression tests and complete CI.

## Deterministic staged recovery harness

The original single-turn recovery prompt required the model to voluntarily execute guard -> write -> read as three separate client-tool calls. The decisive live run recovered and wrote the correct token directly, proving continuity, but did not follow that three-command choreography.

That choreography is now represented by `tools/codex_remote_compaction_recovery_staged.py`, which splits validation into three bounded resumed turns on the same thread:

1. workspace guard;
2. result write using the conversation-retained token;
3. result readback.

Each stage requires exactly one safe client `exec_command`, and the staged gate also checks exact result/readback content and that compaction markers remain stable. This avoids conflating product continuity with one-turn instruction-following variance.

## CI

Security hardening workflow run #473 completed successfully across:

- public repository safety;
- Ubuntu Python 3.11 / 3.13;
- macOS Python 3.11 / 3.13;
- reproducible upstream regression suite.

The staged runner is included in the CI `py_compile` contract and its focused tests are part of the reproducible regression suite.

## Gate decision

P1.2 / merge-critical M1 is **PASS / CLOSED**.

The next merge-critical work is accelerated P1.3 minimal continuity hardening: lost-affinity/restart fallback correctness, stable identity / stale-generation fencing, and uncertain tool-effect reconciliation before retry.

No private token value, thread id, local trace path, local process id, prompt body, command body, or tool output is recorded in this document.
