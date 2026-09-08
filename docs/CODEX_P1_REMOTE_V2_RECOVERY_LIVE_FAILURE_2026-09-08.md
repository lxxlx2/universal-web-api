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

A bounded classification of the private recovery trace showed one normal `agent_message`, no tool item, no error event, no synthetic-token text, and the reply matched the workspace-mismatch sentinel class.

## Root cause confirmed

The recovery prompt used the natural Chinese wording:

```text
第一步必须单独调用一次客户端 exec_command
```

The V2 strict required-tool detector did not recognize that phrase. Its existing compatibility patch recognized direct/client-prefixed forms such as:

```text
必须使用 exec_command
必须通过客户端 exec_command
```

but not the bounded modifiers `单独调用一次客户端`. As a result `required_declared_tool(...)` returned an empty requirement, so the bounded required-tool repair path never ran and a plain-text `ACCEPTANCE_WORKSPACE_MISMATCH` reply escaped as a normal final answer.

This means the first recovery failure is not evidence that remote compaction lost the token.

## Repair

`app/services/codex_required_tool_language_patch.py` now recognizes a deliberately bounded Chinese grammar:

```text
必须/务必/一定要/请务必/只能
+ optional 先/再
+ optional 单独
+ optional 通过/使用/调用/执行
+ optional 一次/一遍/一个
+ optional 客户端
+ declared tool name
```

It still requires the matched tool to be present in the client-declared tool list, and an explanatory sentence such as `你必须解释为什么 exec_command ...` remains non-forcing.

Focused regressions cover both the original `必须通过客户端 exec_command` wording and the exact post-remote recovery wording.

Security hardening #432 / run `34195002230` completed successfully across public-repo-safety, macOS/Ubuntu security matrices, and the full reproducible upstream regression suite.

## Current gate

```text
P1.2 native remote compaction                 PASS
P1.2 recovery required-tool parser repair     PASS / CI
P1.2 same-thread post-remote recovery rerun   CURRENT
```

Rerun only the same-thread recovery gate after restarting UWA to load the language patch. Do not rebuild the large-context thread or repeat remote compaction unless the retained private trace becomes unavailable.
