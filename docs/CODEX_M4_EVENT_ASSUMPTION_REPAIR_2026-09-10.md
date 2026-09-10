# M4 focused regression event-assumption repair — 2026-09-10

## Status

M4 remains open. The latest focused suite again ran three tests: normal completion passed, while consumer cancellation and `aclose()` failed before reaching their cancellation assertions.

## Exact failure

Both remaining failures stopped on the same test-only assumption: the first yielded transport chunk was asserted to contain `response.created`, but the observed local stream chunk was `response.in_progress`.

That means the two tests did not yet exercise the lifecycle assertions they were intended to validate. The failure is therefore in the test harness preamble expectation, not evidence that backing-task cancellation is still broken.

The production cleanup ordering retained for the next run is:

```text
clear workflow reuse hint
cancel unfinished backing task
await the cancelled backing task
swallow only the backing task's CancelledError
allow caller cancellation / generator closure to propagate normally
```

## Repair

`tools/codex_m4_focused_repair_and_close.py` was updated so the lifecycle tests no longer depend on a particular initial Responses event spelling.

The tests now verify only the behavior that matters for this hardening item:

```text
consumer cancellation propagates CancelledError
unfinished backing task is cancelled and awaited
workflow reuse hint ends false
aclose() cleans the backing task
normal completion does not cancel an already-finished worker
normal completion still emits a terminal completed response
```

The `aclose()` test still requires a non-empty progress chunk before closing the generator, but does not require that progress to be represented specifically as `response.created`, `response.in_progress`, or a keepalive comment.

## Next gate

Rerun only the bounded focused closer. Do not rerun the original 719-second M4 coding turn.

M4 closes only after:

```text
focused unittest                              PASS
py_compile                                    PASS
git diff --check                              PASS
bounded read-only Codex/UWA review            turn.completed
real exec_command evidence                    YES
route                                          uwa / chatgpt / high
post-review request-manager                   0
verified implementation + test commit/push    PASS
```
