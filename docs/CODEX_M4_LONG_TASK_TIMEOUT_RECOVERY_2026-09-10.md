# Codex M4 Long-Task Timeout Recovery — 2026-09-10

## Result of first real-project attempt

The first M4 real-project Codex turn passed route and health preconditions and performed substantial real local client-tool activity, but the harness reached its 720-second wall-clock limit before the Codex turn emitted `turn.completed`.

Observed safe metadata:

```text
configured route                         uwa / chatgpt / high
health before                            running=0 / browser connected
route marker                             PASS
Codex elapsed                            719 seconds
Codex event classes                      thread.started, turn.started, item.started, item.completed
real tool item count                     14
stream-disconnect stderr                 absent
workspace after timeout                  only app/api/codex_responses_v2.py modified
request manager after                    running=0
browser after                            connected
```

The controlled ChatGPT Web turn visibly progressed through multiple real `exec_command` calls. Near the timeout it was still probing Python/runtime candidates for validation. The failure is therefore recorded as a bounded pilot completion failure, not as evidence of a transport disconnect or leaked UWA request.

## Recovery decision

Do not discard the workspace and do not rerun another unconstrained 12-minute coding turn.

The recovery path is intentionally deterministic:

1. Accept only the expected partial dirty scope from the first M4 attempt.
2. Rebuild the intended cancellation cleanup from the tracked base so timed-out partial edits cannot survive accidentally.
3. Add a stdlib `unittest` regression suite covering consumer cancellation, `aclose()` after keepalive, and normal completion.
4. Run local tests, `py_compile`, and `git diff --check` outside the Codex sandbox.
5. Run one bounded read-only Codex/UWA review turn with exactly one required `exec_command`; it may not edit files, search for environments, or install dependencies.
6. Verify post-marker `uwa / chatgpt / high`, real client tool evidence, `turn.completed`, and request-manager cleanup.
7. Commit/push only the implementation and regression-test files after every gate passes.

Runner:

```text
tools/codex_m4_resume_after_timeout.py
```

## Why this still exercises the M4 objective

The first long turn already exercised the real repository, real Codex client tools, UWA browser inference, repeated tool-result continuation, and a non-trivial implementation edit. The recovery gate independently validates the resulting runtime behavior and requires a fresh completed real Codex/UWA tool round trip before closure.

M4 must remain open until the recovery runner reports:

```text
M4_REAL_PROJECT_LONG_TASK_PILOT=PASS_LIVE_CLOSED
```

## Safety

Do not publish raw browser prompts, local command bodies/output, thread ids, process ids, private paths, cookies, credentials, or raw wire traces. Public records contain only aggregate route/tool/event/check outcomes and public repository file names.
