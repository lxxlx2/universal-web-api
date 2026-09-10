# M4 completed-review structural gate — 2026-09-10

## Status

`M4` remains open until the structural finalizer commits the validated implementation and regression test, but the latest bounded recovery review itself completed successfully.

Observed safe evidence from the completed review:

```text
focused local regression                PASS 3/3
py_compile                              PASS
git diff --check                        PASS
Codex recovery review RC                0
Codex event flow                        thread.started -> turn.started -> item.started/item.completed -> turn.completed
real local tool item activity           YES
stderr transport errors                 NONE
cosmetic final text marker              absent
```

The missing `M4_RECOVERY_REVIEW_OK` text is not a transport or tool failure. `turn.completed` plus real tool activity and the post-marker metadata-only wire trace provide stronger protocol evidence than a model-authored textual marker.

## Finalization rule

`tools/codex_m4_finalize_completed_review.py` reuses the already-completed review instead of spending another Web turn. It must prove all of the following before any commit:

```text
expected dirty scope only
canonical stream-cancellation cleanup rebuilt from tracked base
stdlib cancellation regressions PASS 3/3
py_compile PASS
git diff --check PASS
fresh route-audit marker present
post-marker agent request present
post-marker route chatgpt / high
post-marker exec_command response present
post-marker completed response present
route audit uwa / chatgpt / high PASS
request-manager running count = 0
browser connected = true
```

Only after those gates pass may it stage, commit and push `app/api/codex_responses_v2.py` and `tests/test_codex_v2_stream_cancellation.py`.

## Safety

This record contains no prompt body, command body, tool output, raw thread/process/browser identifier, account data, cookies, credentials, or full wire trace.
