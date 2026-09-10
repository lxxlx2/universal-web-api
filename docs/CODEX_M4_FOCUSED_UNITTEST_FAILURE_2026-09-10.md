# M4 focused unittest failure — 2026-09-10

## Status

`M4 real-project long-task pilot`: **CURRENT / BLOCKED ON FOCUSED REGRESSION**

## Proven before this point

The real-project pilot has already proven the live UWA route and substantial real client-tool activity. The original long turn ran for the bounded harness window, produced real tool events, did not report a stream-disconnect error, and returned to a clean request-manager/browser state after timeout.

The recovery path then proved:

```text
provider/model/effort                    uwa / chatgpt / high
UWA running count before                 0
browser connected before                 YES
canonical cancellation patch target      unique
canonical implementation written         YES
regression test written                   YES
repository-capable Python selected        YES
py_compile                                PASS
```

## Current blocker

The generated stdlib regression suite ran three tests and returned:

```text
Ran 3 tests
FAILED (failures=2)
```

Therefore M4 is not closed. The bounded Codex review, post-marker route gate, final health gate, commit and push were correctly skipped by the fail-closed recovery runner.

The exact failing assertions were not present in the first sanitized runner output. `tools/codex_m4_focused_unittest_diagnose.py` now performs a read-only detailed rerun and prints sanitized failing test names, traceback/assertion detail, and the local implementation diff hunk. It does not edit, stage, restore, reset, commit or push local files.

## Next action

Run the focused diagnostic against the preserved local M4 artifacts. Use that evidence to determine whether the canonical cancellation cleanup or the regression harness is wrong, then repair only the proven defect. Do not rerun the original 12-minute long task.

## Safety

Do not commit private runtime/session/browser data or raw traces. The diagnostic sanitizes the home-directory prefix and emits only local test/diff evidence needed for this gate.
