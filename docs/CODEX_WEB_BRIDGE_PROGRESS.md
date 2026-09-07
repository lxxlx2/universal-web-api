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

The first aggregate checker run after Stage F returned only `git_diff: FAIL`; the checker repair now scopes Stage C change auditing to tracked diffs under `git_diff/` while still rejecting tracked edits to Stage C tests or requirements.

The operator reran the full checker in the existing workspace without cleaning generated artifacts and obtained:

```text
multi_file: PASS
failure_recovery: PASS
git_diff: PASS
interactive: PASS
context: PASS
ACCEPTANCE_PASS
```

Detailed record: `docs/CODEX_FULL_ACCEPTANCE_HARNESS_FALSE_FAILURE_2026-09-07.md`.

## P1 discovery: compact endpoint prerequisite

Before generating large synthetic context, the current upstream Codex compaction path was inspected. Remote compaction posts to:

```text
/v1/responses/compact
```

and the current Codex client consumes a JSON `output` array of Responses items. Compaction is also observable through context-compaction lifecycle items.

Current UWA branch inspection found no `/v1/responses/compact` route in the V2 adapter, legacy Codex Responses adapter, or generic Responses adapter. This is classified as a P1 protocol blocker, not an A-F regression.

Detailed record: `docs/CODEX_P1_RESPONSES_COMPACT_GAP_2026-09-07.md`.

## Current gate

```text
Stage A-F live acceptance                 PASS
aggregate A-F checker                     PASS
P1 compact contract inspection            DONE
local /v1/responses/compact runtime probe  NEXT
compact endpoint implementation           pending
large-context compaction stress            blocked on protocol support
```

## Production-hardening roadmap

```text
P1.0 compact runtime probe
P1.1 compact endpoint + regression + CI
P1.2 large-context compaction / stress / recovery
P1.3 lost-affinity / restart fallback deeper validation
P1.4 real-project long-task pilot
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
