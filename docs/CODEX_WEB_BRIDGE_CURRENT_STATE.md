# Codex Web Bridge current state

Canonical handoff for `codex-web-bridge-v2`.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while routing model inference through UWA to logged-in ChatGPT Web. Codex remains authoritative for filesystem, shell, edits, tests, Git, sandbox and approval.

## Verified live acceptance

```text
single-file coding loop                    PASS
Stage A multi-file read/edit/test          PASS
Stage B failure recovery                   PASS
Stage C Git diff discipline                PASS
Stage D long process + write_stdin         PASS
Stage E same-thread context                PASS
Stage F Codex + UWA restart continuity     PASS
real exec_command / native cwd             PASS
Responses tool round trip                  PASS
required-tool enforcement                  PASS
call-id / web-session continuation         PASS
```

Stage F crossed a real UWA restart. Process-local affinity was confirmed destroyed (`binding_count=4 -> 0`), then the same Codex thread resumed without repeating the token, executed a real local command, restored `EMBER-7319\n`, returned `CONTEXT_PASS`, and passed the independent checker.

## Aggregate A-F regression incident

After Stage F closure, the operator ran:

```bash
python3 tools/codex_desktop_acceptance.py check
```

Results:

```text
multi_file: PASS
failure_recovery: PASS
git_diff: FAIL
interactive: PASS
context: PASS
ACCEPTANCE_FAIL count=1
```

The Stage C evidence inside the failure was still healthy:

```text
values_ok=True
diff_check=0
```

The only unexpected paths were harness/runtime artifacts outside the Stage C scope: regenerated `PROMPTS.md`, Python `__pycache__`, and `.pyc` files. This is classified as a harness false failure, not a bridge or Stage C regression.

Detailed record:

`docs/CODEX_FULL_ACCEPTANCE_HARNESS_FALSE_FAILURE_2026-09-07.md`

## Repair applied

`tools/codex_desktop_acceptance.py` now evaluates Stage C tracked changes only under `git_diff/` and still allows only:

```text
git_diff/config.py
```

A tracked edit to `git_diff/tests/*`, `git_diff/REQUIREMENTS.txt`, or another Stage C path still fails the checker. Other scenarios' artifacts and runtime cache files no longer contaminate the Stage C verdict.

Regression coverage was added for both cases:

1. aggregate workspace artifacts outside `git_diff/` must not fail Stage C;
2. tracked Stage C test edits must still be rejected.

Current code head containing the repair: `d9543b5`.

CI run #195 is validating that head. A local aggregate rerun is required after CI passes before P1 begins.

## Continuity layers

1. Codex Desktop / CLI thread history.
2. Private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Git tracked handoff documents as long-term project truth.

## Current priority

```text
P0 finish aggregate A-F checker repair and local rerun
P1 large-context compaction / stress / recovery
P1 lost-affinity / restart fallback deeper validation
P1 real-project long-task pilot
P2 concurrent request / queue / controlled-tab hardening
P3 MCP/plugin namespace and multi-agent/tool fan-out
P4 Responses SSE slimming and transcript hygiene
P5 final regression, operator docs and release checklist
```

Large-context validation is intentionally blocked until the aggregate A-F checker is clean again.

## Collaboration rule

Every completed stage, important failure, repair and disruptive checkpoint is committed before moving on. README, this canonical state, progress tracking, stage/failure records and Draft PR should remain aligned.

## Merge policy

Do not merge into `main` yet. Merge only after production-hardening gates, real-project pilot, final regression, CI, documentation and public-repository safety checks are green.

## Public repository safety

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, Codex memory workspace content, or private project source captured during acceptance.
