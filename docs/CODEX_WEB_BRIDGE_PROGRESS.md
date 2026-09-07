# Codex Web Bridge Progress

## Branches

- stable verified base: `security-hardening`
- active V2 development: `codex-web-bridge-v2`
- V2 Draft PR: #2

## Verified macOS milestones

```text
single-file coding loop                     PASS
Stage A multi-file coding loop              PASS
Stage B failure recovery                    PASS
Stage C Git diff discipline                 PASS
Stage D long process + write_stdin          PASS
Stage E same-thread context continuity      PASS
Stage F Codex + UWA restart continuity      PASS
aggregate A-F checker                       PASS
real exec_command / native cwd              PASS
Responses function_call round trip          PASS
required-tool repair                        PASS
duplicate required-tool suppression         PASS
call-id continuation affinity               PASS
single-tool / single-web-conversation gate  PASS
```

## Aggregate checker false failure: CLOSED

The first aggregate checker run after Stage F returned only `git_diff: FAIL`. The Stage C implementation evidence was still healthy (`values_ok=True`, `diff_check=0`), and the unexpected paths were generated `PROMPTS.md`, `__pycache__`, and `.pyc` artifacts outside Stage C.

Repair commits:

```text
b9235d9  Scope git diff acceptance to Stage C tracked files
d9543b5  Cover aggregate Stage C checker artifacts
```

The repaired checker now audits tracked diffs only under `git_diff/` and still requires `git_diff/config.py` to be the sole tracked Stage C modification.

The operator reran the full checker in the existing workspace without cleaning generated artifacts and obtained:

```text
multi_file: PASS
failure_recovery: PASS
git_diff: PASS
interactive: PASS
context: PASS
ACCEPTANCE_PASS
```

This closes the incident and proves the fix addresses the real aggregate-workspace shape rather than a freshly cleaned fixture.

Detailed record:

`docs/CODEX_FULL_ACCEPTANCE_HARNESS_FALSE_FAILURE_2026-09-07.md`

## Current gate

```text
Stage A-F live acceptance                 PASS
post-Stage-F aggregate checker            PASS
harness repair implementation             DONE
regression coverage                        DONE
P1 large-context acceptance                NEXT
```

## Production-hardening roadmap

```text
P1 large-context compaction / stress / recovery
P1 lost-affinity / restart fallback deeper validation
P1 real-project long-task pilot
P2 concurrent request / queue / controlled-tab hardening
P3 advanced MCP/plugin namespace coverage
P3 multi-agent/tool fan-out coverage
P4 successful Responses SSE payload slimming
P4 ChatGPT Web transcript hygiene
P5 final acceptance regression
P5 operator docs / release checklist
```

## Recording discipline

Every live result, failure, repair and disruptive checkpoint must be committed before the next step. README, canonical current state, this file, stage/failure records and Draft PR must stay aligned.

## Final merge plan

Merge `codex-web-bridge-v2` into `main` only after the production-hardening gates, real-project pilot, final regression, CI and repository-safety checks are green and the handoff documentation is current.
