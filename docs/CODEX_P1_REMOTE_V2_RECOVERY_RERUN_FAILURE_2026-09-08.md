# P1.2 post-remote recovery rerun failure — 2026-09-08

## Classification

FAIL — the required-tool language patch was loaded successfully and the UWA / remote-V2 provider preconditions remained valid, but the resumed Codex recovery turn exited with client return code 1 before producing a recoverable structured result.

This does not invalidate the preceding native remote-compaction live PASS.

## Preconditions confirmed

```text
HEALTH_PASS=YES
REMOTE_COMPACTION_COMPAT=ENABLED
REQUIRED_TOOL='exec_command'
REQUIRED_TOOL_PATCH_PASS=YES
PRIVATE_TRACE_DIR_VALID=YES
PRIVATE_THREAD_RECOVERED=YES
PRIOR_TRIGGER_CONTRACT=PASS
ROLLOUT_COMPACT_MARKERS_PRE_RECOVERY=1
TOKEN_LEAK_BEFORE_RECOVERY=NO
```

## Failure evidence

```text
RUN_FAIL recovery_turn=Codex turn failed rc=1; private trace=<private local path>
```

The recovery runner failed before it could emit `SAME_THREAD`, tool-call counts, or result-file checks for this rerun. Therefore the current blocker is now the client/runtime error path for the resumed recovery turn, not the previously repaired required-tool wording detector.

## Next diagnostic

Do not rerun the recovery gate blindly. Inspect only the bounded, sanitized event/error shape from the private `post-remote-recovery.jsonl` trace. The diagnostic must not print prompts, thread ids, response bodies, synthetic tokens, commands, session paths, rollout contents, or private tool outputs.

Current gate:

```text
P1.2 native remote compaction                 PASS
P1.2 required-tool wording parser             PASS / CI PASS
P1.2 same-thread post-remote recovery         FAIL / runtime diagnosis CURRENT
```
