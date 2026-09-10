# Codex M4 Real-Project Long-Task Gate — 2026-09-10

## Status

CURRENT.

M3a Hybrid Routing Safety H0-H5 and M3b Desktop D1-D5 are closed. The next release-critical gate is one non-trivial coding task on the real Codex Web Bridge repository through the verified UWA route.

## Selected task

Use the real repository to close a known runtime-hardening item in the streamed V2 Responses path.

`_stream_codex_v2_attempt` creates a backing async task for `_run_chat_completion_final`. If the outer ASGI/async generator is cancelled or closed before that task finishes, cleanup must guarantee the backing task cannot remain alive as orphan browser/request work.

Required behavior:

```text
normal completion
→ unchanged Responses/event/affinity behavior

outer generator cancellation or premature close
→ if backing task is still pending, cancel it
→ await its cancellation/termination
→ do not leave background browser/request work alive
→ do not swallow caller cancellation
```

## Pilot acceptance

The pilot must prove all of the following:

```text
project branch clean before work                   YES
configured route                                   uwa / chatgpt / high
UWA health before                                  healthy / running=0
fresh route marker                                 YES
real Codex agent turn                              turn.completed
real exec_command client call                      YES
implementation changed                             app/api/codex_responses_v2.py
regression test added                              tests/test_codex_v2_stream_cancellation.py
stdlib focused tests                               PASS
py_compile                                         PASS
git diff --check                                   PASS
no unrelated changed/new files                    YES
post-marker route                                  uwa / chatgpt / high
UWA health after                                   running=0
verified diff committed/pushed only after checks   YES
```

The Codex agent must not commit or push by itself. The one-shot runner performs guarded staging/commit/push after independent local checks. Transient Python bytecode/cache files are excluded from the scope comparison; all substantive extra files still fail closed.

## Safety

The public acceptance record may contain only aggregate event/tool counts, changed public file names, route metadata and check outcomes. Do not commit raw Codex stdout, private prompts, tool bodies/output, browser/session identifiers, PIDs, credentials, cookies or private wire traces.

## Runner

```text
tools/codex_m4_real_project_pilot_safe.py
```

The safe wrapper delegates to the guarded M4 runner and only filters transient `__pycache__`, `.pyc` and `.pytest_cache` files from ignored-file delta checks.

After PASS, M4 closes and the release path advances to M5 final A-F + compaction + restart regression.
