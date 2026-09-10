# M5 Stage A-F replay setup ownership fix — 2026-09-10

## Observed live failure

The second M5 live attempt successfully passed branch, route, Codex CLI, validation-Python and private-pytest preconditions, but stopped at the fresh Stage A-F replay setup step:

```text
VALIDATION_RUNTIME_READY=YES
VALIDATION_PYTEST_SOURCE=PRIVATE_BOOTSTRAP
M5_PRIVATE_PYTEST_BOOTSTRAP=CACHED
VALIDATION_PYTHON_READY=YES
M5_STAGE_A_F_REPLAY_SETUP_RC=1
M5_STAGE_A_F_REPLAY_CLEANED=YES
M5_FINAL_REGRESSION=FAIL
M5_FAILURE_CLASS=stage_a_f_replay_setup_failed
```

No product correctness regression, UWA restart, or Codex live continuity turn had started at that point.

## Root cause

`tools/codex_m5_final_regression_safe_v2.py` allocated the private replay path by creating the directory and placing the M5 replay marker before invoking `tools/codex_desktop_acceptance.py setup`.

The acceptance harness intentionally refuses to touch an already-existing directory unless it contains the acceptance harness marker `.uwa_codex_acceptance`. The M5-owned marker is a different marker, so the setup command correctly failed closed.

This is an ownership/fixture-construction bug in the M5 wrapper. It is not evidence that the already-closed Stage A-F product acceptance regressed.

## Repair

The replay allocator now returns a unique non-existing child path under private `~/.uwa/m5-stage-af-replay` state. The acceptance harness is therefore the component that creates and marks the workspace.

Only after acceptance setup succeeds does M5 add its own private replay ownership marker and materialize the deterministic completed-state fixture.

Cleanup accepts either the M5 replay marker or the acceptance harness marker, but only for an exact direct child of the private replay parent. This keeps failure cleanup bounded if setup creates a partial owned workspace and then exits early.

A regression test now exercises the exact sequence with a temporary private parent:

```text
fresh replay path does not pre-exist
acceptance setup succeeds
M5 ownership marker is added
aggregate Stage A-F replay passes
private replay workspace is removed
```

## Release classification

M5 remains `CURRENT`.

The previous live run remains useful evidence that:

```text
repository precondition                     PASS
uwa / chatgpt / high configuration          PASS
Codex CLI                                   PASS
runtime-capable Python                       PASS
private pytest bootstrap                     PASS / cached
```

The next M5 run should proceed through the repaired Stage A-F replay setup before entering the complete current Codex regression family and restart-continuity live smoke.
