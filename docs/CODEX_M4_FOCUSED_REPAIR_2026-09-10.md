# M4 focused cancellation repair

Date: 2026-09-10

## Trigger

The deterministic M4 timeout-recovery path reached local regression execution and ran three stdlib async-stream tests. One passed and two failed.

Sanitized failures:

```text
test_aclose_cleans_backing_task_after_keepalive        FAIL
test_consumer_cancellation_cleans_backing_task         FAIL
test_normal_completion_does_not_cancel_finished_worker PASS
```

## Diagnosis

The failures isolate two separate issues.

First, the explicit `aclose()` test overconstrained the transport-progress representation. The observed next event was `response.in_progress` while the test required the literal substring `keepalive`. M4 is validating backing-task lifecycle, so the test should accept either supported non-terminal progress representation and then verify that `aclose()` cancels the backing worker and clears reuse state.

Second, the consumer-cancellation path proved that cleanup ordering can leave the workflow reuse hint true at the assertion point even though the backing worker has already received cancellation. The focused repair clears the reuse hint immediately on generator unwind, before the cancellation-sensitive await of the backing task, then cancels and awaits the backing task. Caller cancellation must still propagate.

The consumer-cancellation test is also made deterministic by using a long heartbeat interval, preventing a heartbeat race from winning before the cancellation injection. The `aclose()` test intentionally uses a short heartbeat interval so the generator is suspended at a non-terminal progress yield before explicit closure.

## Repair runner

`tools/codex_m4_focused_repair_and_close.py`

The runner reuses the safe timeout-recovery pipeline and performs the complete remaining M4 closure flow:

```text
strict resume-state checks
UWA readiness
canonical focused implementation rewrite
three deterministic stdlib regression tests
py_compile
git diff --check
bounded read-only Codex/UWA review
real exec_command evidence
post-marker uwa / chatgpt / high verification
request-manager clean postcondition
commit and push of only implementation + regression test
```

If any local regression still fails, the runner prints the failing test names and a bounded diagnostic tail and stops before the live review or Git mutation.

## Status

M4 remains open until the focused closer reports:

```text
M4_REAL_PROJECT_LONG_TASK_PILOT=PASS_LIVE_CLOSED
```
