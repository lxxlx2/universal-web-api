# Full acceptance harness false failure — 2026-09-07

## Context

After Stage F was closed as PASS, the operator ran the aggregate acceptance checker:

```bash
python3 tools/codex_desktop_acceptance.py check
```

Observed result:

```text
multi_file: PASS
failure_recovery: PASS
git_diff: FAIL
interactive: PASS
context: PASS
ACCEPTANCE_FAIL count=1
```

## Failure classification

This is classified as a harness false failure, not a Stage C bridge regression.

The `git_diff` checker reported:

```text
values_ok=True
diff_check=0
```

So the Stage C implementation values were correct and `git diff --check` was clean.

The failure came only from the aggregate workspace-status filter treating harness/runtime artifacts as unexpected changes:

- regenerated `PROMPTS.md` after the acceptance harness changed;
- Python `__pycache__` directories;
- generated `.pyc` files from running the test suites.

These files are not Stage C implementation edits and should not invalidate the Git-discipline checker.

## Root cause

`_check_git_diff()` calls `_changed_paths()`, which currently uses:

```text
git status --porcelain=v1 --untracked-files=all
```

and then compares every returned path against a static allowlist. The allowlist contains prior scenario result artifacts but does not exclude deterministic Python cache files or the harness-generated `PROMPTS.md`.

This remained hidden during the isolated Stage C run because those later aggregate artifacts were not all present yet. It surfaced only after running the complete A-F workspace through the aggregate checker.

## Required repair

The harness repair must remain narrow:

1. ignore generated Python cache artifacts (`__pycache__` and `.pyc`) when evaluating acceptance-workspace changes;
2. treat harness-owned `PROMPTS.md` as allowed aggregate metadata;
3. continue rejecting unexpected implementation/test/source edits;
4. add regression coverage reproducing this exact aggregate-workspace shape;
5. rerun CI and then rerun the full local acceptance checker.

## Status

```text
Stage A-F live acceptance          PASS
post-Stage-F aggregate check       FAIL (harness false failure)
harness repair                     IN PROGRESS
full aggregate rerun               pending
large-context acceptance           blocked until aggregate checker is clean
```

The aggregate failure is recorded before applying the repair so another collaborator can recover the exact state from Git.
