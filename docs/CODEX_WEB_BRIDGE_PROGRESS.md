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

Evidence note: the final Stage E/F runs were audited primarily through `codex exec` / `codex exec resume`. They close the protocol/CLI continuity gate but do not close actual ChatGPT Desktop UI acceptance. A mandatory Desktop D1-D5 gate has now been added in `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`.

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

## P1 compact endpoint prerequisite

Before generating large synthetic context, upstream Codex compaction behavior was inspected. Remote compaction posts to:

```text
/v1/responses/compact
```

The current Codex client consumes a JSON `output` array of Responses items and exposes compaction through observable lifecycle items.

Code inspection found no matching UWA route. The real macOS runtime probe then confirmed:

```text
COMPACT_ROUTE_REGISTERED=NO
HTTP/1.1 404 Not Found
```

P1.0 is closed. P1.1 implementation is current.

Detailed record: `docs/CODEX_P1_RESPONSES_COMPACT_GAP_2026-09-07.md`.

## Official Codex Desktop recovery

A safe helper now exists:

```text
tools/codex_provider_switch.py
```

Its `official` action backs up `~/.codex/config.toml`, removes only top-level provider/model/reasoning pins, keeps the UWA provider definition, and leaves authentication untouched. The restored Desktop session is intentionally model-agnostic; the signed-in account/workspace controls which models can be selected.

## Current gate

```text
Stage A-F protocol/CLI acceptance          PASS
aggregate A-F checker                      PASS
P1 compact contract inspection             DONE
local /v1/responses/compact runtime probe  DONE: 404 confirmed
compact endpoint implementation            IN PROGRESS
large-context compaction stress            blocked on compact protocol support
Desktop UI live gate D1-D5                 pending / mandatory before main
```

## Production-hardening roadmap

```text
P1.1 compact endpoint + regression + CI
P1.2 large-context compaction / stress / recovery
P1.3 lost-affinity / restart fallback deeper validation
Desktop D1-D5 actual UI acceptance
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

Merge `codex-web-bridge-v2` into `main` only after compact/large-context/restart hardening, actual Desktop UI acceptance, the real-project pilot, final regression, CI and repository-safety checks are green and the handoff documentation is current.
