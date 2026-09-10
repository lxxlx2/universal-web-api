# M4 real-project long-task pilot — LIVE PASS — 2026-09-10

## Result

M4 is **PASS / LIVE / CLOSED**.

The real-project pilot used the active `universal-web-api` repository, the managed `uwa / chatgpt / high` route, real Codex client-tool execution, and the production V2 streamed Responses path. The final implementation closes the async-generator cancellation/orphan-task gap and passed deterministic regression plus live structural validation.

## Production change

The accepted production change is intentionally narrow:

```text
app/api/codex_responses_v2.py
tests/test_codex_v2_stream_cancellation.py
```

When `_stream_codex_v2_attempt()` unwinds, it clears the workflow-reuse hint and, if the backing `_run_chat_completion_final()` task is still pending, cancels and awaits that task. `asyncio.CancelledError` from the backing task is consumed only as cleanup of the task that this generator has cancelled; caller cancellation still propagates from the generator operation itself.

The normal-completion path leaves an already-finished worker alone.

Accepted implementation commit:

```text
38554bd9d2301783d1bc2d9aff8005c60c70f389
Harden Codex V2 stream cancellation cleanup
```

## Deterministic regression evidence

The final local gate passed all three lifecycle cases:

```text
consumer cancellation propagates + backing task cleanup       PASS
explicit async-generator aclose() cleanup                     PASS
normal completion without spurious worker cancellation        PASS
py_compile                                                    PASS
git diff --check                                              PASS
validated changed-path scope                                  PASS
```

The focused suite uses stdlib `unittest` and does not depend on a specific preamble Responses event spelling.

## Live structural evidence

The earlier real-project Codex turn exercised sustained local tool/result continuation for 719 seconds and produced 14 real tool-item events without a stream-disconnect failure. Its timeout left request-manager state clean and the browser connected.

The bounded recovery review subsequently reached a completed Codex turn. Final structural validation proved all release-relevant facts without requiring a cosmetic model-authored text marker:

```text
post-marker agent request count                  1
post-marker agent response count                 1
post-marker route                               chatgpt / high
post-marker completed response                  present
Responses function_call_output evidence         present
Codex rollout command-event evidence            present
route audit                                     uwa / chatgpt / high PASS
final request-manager running count             0
final browser connection                        healthy
```

The metadata-only response summary did not contain an `exec_command` function-call name for this completed review. That single field is not used as a sole source of truth because the same bounded review has independent real-tool proof from both the returned `function_call_output` and a timestamped Codex command-execution event.

No prompt body, command body, tool output, raw thread id, rollout path, process id, browser id, cookie, credential, account identifier, or private trace content is recorded here.

## Gate decision

```text
M1   PASS / CLOSED
M2   PASS / CLOSED
M3a  PASS / LIVE / CLOSED
M3b  PASS / LIVE / CLOSED
M4   PASS / LIVE / CLOSED
M5   CURRENT
M6   pending
M7   pending
```

M5 is the final aggregate regression gate: existing Stage A-F acceptance, current compaction/continuity regression coverage, and a fresh post-restart UWA/Codex continuity smoke on the final M4 code.
