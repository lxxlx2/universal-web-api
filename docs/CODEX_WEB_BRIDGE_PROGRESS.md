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

Initial inspection and live runtime evidence showed:

```text
COMPACT_ROUTE_REGISTERED=NO
HTTP/1.1 404 Not Found
```

P1.0 therefore closed with the endpoint confirmed absent.

P1.1 implementation added `app/api/codex_compact.py` plus `tests/test_codex_responses_compact.py`. GitHub Actions Security hardening run #220 at implementation/test head `5cccbcf4b7f5f0c53467423ce1e5250c7fc1457d` completed with `success`.

The first post-implementation macOS live probe then produced:

```text
COMPACT_ROUTE_REGISTERED=YES
COMPACT_HTTP_CODE=500
JSON_PARSE=PASS
OUTPUT_IS_LIST=NO
OUTPUT_COUNT=0
MARKER_PRESERVED=NO
TASK_PRESERVED=NO
```

The local traceback has now closed the diagnostic uncertainty:

```text
TypeError: SecureLogger.info() takes 2 positional arguments but 3 were given
```

The backing compact request and assistant replacement output had already succeeded. The request failed only on the final success log because `app/api/codex_compact.py` used stdlib logging interpolation arguments against UWA's one-argument `SecureLogger`. The backing-error `logger.warning()` branch had the same latent incompatibility.

The narrow repair is now on the active branch:

- compact success/error logging uses single preformatted messages;
- route-level success regression uses an `info(message)` logger;
- route-level backing-error regression uses a `warning(message)` logger;
- compact protocol behavior itself is unchanged.

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
pre-repair compact regression + CI         PASS
post-implementation compact runtime probe  FAIL: HTTP 500
compact traceback root cause               CONFIRMED: SecureLogger signature
SecureLogger repair + route regressions    DONE
repair CI                                  NEXT
post-repair macOS direct compact rerun      blocked on CI
large-context compaction stress            BLOCKED
Desktop UI live gate D1-D5                 pending / mandatory before main
```

## Production-hardening roadmap

```text
P1.1 repair CI + direct compact live rerun
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
