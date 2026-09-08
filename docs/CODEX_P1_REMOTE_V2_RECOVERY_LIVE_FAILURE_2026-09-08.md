# P1.2 post-remote recovery live failure — 2026-09-08

## Classification

FAIL — same-thread recovery reached the compacted Codex thread, but no local tool call was emitted and the synthetic conversation-only token was not recovered into the acceptance result file.

This does **not** invalidate the preceding native remote-compaction live PASS.

## Preconditions / retained evidence

The dedicated recovery runner verified:

```text
PRIVATE_TRACE_DIR_VALID=YES
PRIVATE_THREAD_RECOVERED=YES
PRIOR_TRIGGER_CONTRACT=PASS
ROLLOUT_COMPACT_MARKERS_PRE_RECOVERY=1
TOKEN_LEAK_BEFORE_RECOVERY=NO
SAME_THREAD=YES
```

Therefore the recovery attempt resumed the same compacted Codex thread and the synthetic token was still absent from the acceptance workspace before the recovery turn.

## Failure evidence

```text
RECOVERY_REPLY_EXACT=NO
RECOVERY_EXEC_COMMAND_COUNT=0
RECOVERY_COMMANDS_SAFE=YES
WORKSPACE_GUARD_OBSERVED=NO
SEPARATE_EXEC_STEPS=NO
RESULT_REFERENCED_TWICE=NO
READ_BACK_OBSERVED=NO
RESULT_EXACT=NO
POST_REMOTE_RECOVERY_FAIL
```

The immediate failure boundary is the recovery turn itself: Codex produced no `exec_command` item, so the required workspace guard / write / read sequence never began.

## What is not yet known

The current public evidence is insufficient to distinguish among:

1. the compacted summary no longer retained the original conversation-only token;
2. the recovery turn refused or ignored the required tool contract;
3. the resumed turn did not expose the expected client tools to the web bridge;
4. another bridge/runtime contract caused a text-only response instead of a structured tool call.

Do not rerun the recovery gate blindly. First inspect the private recovery JSONL through a bounded sanitizer that reports only safe event types, final-response classification, usage and tool-availability metadata without printing the token, prompt, thread id, session path or private bodies.

## Current gate

```text
P1.2 native remote compaction                 PASS
P1.2 same-thread post-remote recovery         FAIL / diagnosis CURRENT
```
