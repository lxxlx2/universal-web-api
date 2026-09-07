# Full acceptance harness false failure — 2026-09-07

## Context

After Stage F was closed as PASS, the operator ran:

```bash
python3 tools/codex_desktop_acceptance.py check
```

Initial result:

```text
multi_file: PASS
failure_recovery: PASS
git_diff: FAIL
interactive: PASS
context: PASS
ACCEPTANCE_FAIL count=1
```

## Classification

This was a harness false failure, not a Stage C bridge regression.

The failing checker also reported:

```text
values_ok=True
diff_check=0
```

The only unexpected paths were outside the Stage C implementation scope:

- regenerated `PROMPTS.md`;
- Python `__pycache__` directories;
- generated `.pyc` files.

## Root cause

The Stage C checker used whole-workspace status and compared every path against a static allowlist. That made the Stage C verdict depend on artifacts produced later by other scenarios and by Python itself.

The Stage C acceptance contract is narrower: verify the intended config values, require `git diff --check`, and ensure tracked changes inside `git_diff/` only touch `git_diff/config.py`.

## Repair

`tools/codex_desktop_acceptance.py` now scopes the Stage C change audit to tracked diffs under `git_diff/` and accepts only:

```text
git_diff/config.py
```

Other scenario result files, regenerated prompt metadata, and untracked runtime caches no longer contaminate Stage C. A tracked edit to `git_diff/tests/*`, `git_diff/REQUIREMENTS.txt`, or any other tracked Stage C path still fails.

Regression coverage in `tests/test_codex_desktop_acceptance_harness.py` verifies both sides:

1. outside-scenario/runtime artifacts do not fail a valid Stage C result;
2. a tracked Stage C test edit is rejected.

Repair commits:

```text
b9235d9  Scope git diff acceptance to Stage C tracked files
d9543b5  Cover aggregate Stage C checker artifacts
```

## Final rerun

The operator intentionally reran the complete checker in the existing acceptance workspace without cleaning the runtime artifacts that triggered the original false failure.

Final result:

```text
multi_file: PASS
failure_recovery: PASS
git_diff: PASS
interactive: PASS
context: PASS
ACCEPTANCE_PASS
```

This proves the repair handles the real aggregate-workspace shape and closes the false-failure incident.

## Status

```text
Stage A-F live acceptance          PASS
post-Stage-F aggregate check       PASS
harness repair                     DONE
regression coverage                DONE
aggregate incident                 CLOSED
P1 large-context acceptance        NEXT
```

The original failure, diagnosis, repair, regression coverage and successful rerun are all retained in Git so the complete problem chain is recoverable by another collaborator.
