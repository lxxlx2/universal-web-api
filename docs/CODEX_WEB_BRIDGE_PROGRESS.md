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

Evidence note: the final Stage E/F runs were audited primarily through `codex exec` / `codex exec resume`. They close the protocol/CLI continuity gate but do not close actual ChatGPT Desktop UI acceptance. A mandatory Desktop D1-D5 gate is tracked in `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`.

## Aggregate checker false failure: CLOSED

The operator reran the repaired full checker in the existing workspace without cleaning generated artifacts and obtained:

```text
multi_file: PASS
failure_recovery: PASS
git_diff: PASS
interactive: PASS
context: PASS
ACCEPTANCE_PASS
```

Detailed record: `docs/CODEX_FULL_ACCEPTANCE_HARNESS_FALSE_FAILURE_2026-09-07.md`.

## P1 compact protocol

P1.0 confirmed the compact endpoint was initially absent. P1.1 then implemented `POST /v1/responses/compact`.

The first post-implementation macOS probe returned HTTP 500. Its first traceback root cause was:

```text
TypeError: SecureLogger.info() takes 2 positional arguments but 3 were given
```

The backing compact request and assistant replacement output had already succeeded. The endpoint used stdlib logging interpolation arguments against UWA's one-argument `SecureLogger`; the backing-error warning branch had the same latent issue.

The first narrow repair changed success/error logging to single preformatted messages and added route-level success/error regressions. Security hardening CI #239 for repair code commit `7c6d7ff` completed with `success`.

The operator then pulled through `b3f37ac`, verified the repaired logger line locally, restarted UWA, confirmed health and route registration, and reran the exact same direct probe. It still returned:

```text
COMPACT_ROUTE_REGISTERED=YES
COMPACT_HTTP_CODE=500
JSON_PARSE=PASS
OUTPUT_IS_LIST=NO
OUTPUT_COUNT=0
MARKER_PRESERVED=NO
TASK_PRESERVED=NO
```

The first logger defect is repaired and deployed. A second unhandled runtime path remains, and its root cause is intentionally unknown until the fresh post-repair traceback is captured.

Detailed records:

- `docs/CODEX_P1_RESPONSES_COMPACT_GAP_2026-09-07.md`
- `docs/CODEX_P1_COMPACT_LIVE_500_2026-09-07.md`

## Official Codex Desktop recovery

`tools/codex_provider_switch.py official` backs up `~/.codex/config.toml`, removes only top-level provider/model/reasoning pins, keeps the UWA provider definition, and leaves authentication untouched. After Desktop restarts, the signed-in account/workspace controls which models are available; the restore path intentionally does not pin Astra, GPT-5.6 Sol, reasoning effort, or any other model setting.

## Current gate

```text
Stage A-F protocol/CLI acceptance          PASS
aggregate A-F checker                      PASS
P1 initial compact runtime probe           DONE: 404 confirmed
compact endpoint implementation            DONE
first compact runtime probe                FAIL: HTTP 500
first root cause                           CONFIRMED: SecureLogger signature
first repair + route regressions           DONE
first repair CI                            PASS: #239
post-repair compact runtime probe          FAIL: HTTP 500
second traceback / root cause              CURRENT / UNKNOWN
large-context compaction stress            BLOCKED until live compact PASS
Desktop UI live gate D1-D5                 pending / mandatory before main
```

## Production-hardening roadmap

```text
P1.1 capture second compact traceback and repair exact path
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
