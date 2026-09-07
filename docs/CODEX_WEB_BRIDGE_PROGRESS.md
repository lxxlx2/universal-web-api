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
real exec_command / native cwd              PASS
Responses function_call round trip          PASS
required-tool repair                        PASS
duplicate required-tool suppression         PASS
call-id continuation affinity               PASS
single-tool / single-web-conversation gate  PASS
```

## Latest incident: aggregate checker false failure

After Stage F passed, the full local checker returned:

```text
multi_file: PASS
failure_recovery: PASS
git_diff: FAIL
interactive: PASS
context: PASS
ACCEPTANCE_FAIL count=1
```

The failing Stage C checker still reported:

```text
values_ok=True
diff_check=0
```

Unexpected paths consisted of `PROMPTS.md`, `__pycache__`, and `.pyc` artifacts outside the Stage C implementation scope. Classification: **harness false failure**, not a bridge regression.

Detailed record:

`docs/CODEX_FULL_ACCEPTANCE_HARNESS_FALSE_FAILURE_2026-09-07.md`

## Repair

The Stage C checker has been narrowed to tracked diffs under `git_diff/` only. It still requires `git_diff/config.py` to be the sole tracked Stage C modification.

Regression tests now verify:

- other scenario results, regenerated prompt metadata, and Python runtime caches do not invalidate Stage C;
- tracked edits under `git_diff/tests/` are still rejected.

Repair commits:

```text
b9235d9  Scope git diff acceptance to Stage C tracked files
d9543b5  Cover aggregate Stage C checker artifacts
```

## Current gate

```text
Stage A-F live acceptance                 PASS
post-Stage-F aggregate checker            FAIL, classified harness bug
harness repair implementation             DONE
regression tests added                     DONE
CI on repaired branch                      RUNNING / verify latest head
local aggregate checker rerun              NEXT
P1 large-context acceptance                blocked until aggregate rerun PASS
```

## Production-hardening roadmap

```text
P0 aggregate A-F rerun clean
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

Merge `codex-web-bridge-v2` into `main` only after the production-hardening gates, real-project pilot, final regression, CI, documentation and repository-safety checks are green.
