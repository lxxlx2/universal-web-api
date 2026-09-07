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
P1.1 Responses compact direct live          PASS
versioned UWA lifecycle CI                  PASS
versioned UWA lifecycle macOS live          PASS
versioned UWA provider switch CI            PASS
versioned UWA provider switch macOS live    PASS
```

Evidence note: the final Stage E/F runs were audited primarily through `codex exec` / `codex exec resume`. They close the protocol/CLI continuity gate but do not close actual ChatGPT Desktop UI acceptance. A mandatory Desktop D1-D5 gate is tracked in `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`.

## Aggregate checker false failure: CLOSED

The repaired full checker in the existing workspace passed every scenario plus `ACCEPTANCE_PASS`.

## P1 compact protocol: CLOSED PASS

P1.0 confirmed `/v1/responses/compact` was initially absent. P1.1 implemented the route. The first live HTTP 500 was traced to stdlib-style multi-argument logging against UWA's one-argument `SecureLogger`; the repair and route-level regressions passed CI.

The apparent recurrence was stale runtime state: the real TCP 8199 listener predated the repair. After proving the port empty, starting a different UWA PID and rerunning the unchanged probe, the real macOS runtime returned HTTP 200 with valid assistant `output`, preserving both the marker and compact task semantics.

## UWA lifecycle hardening: CLOSED PASS

The old local scripts were inspected and their failure mode was reproduced from source:

1. old `codex-uwa-stop` did not prove TCP 8199 was empty after TERM and had no required KILL escalation;
2. old `codex-uwa` reused a healthy listener rather than requiring a fresh process, allowing stale loaded bytecode after repository updates.

The lifecycle implementation is repository-tracked in `tools/codex_uwa_lifecycle.py`, while `tools/install_codex_uwa_commands.py` installs thin `~/bin/codex-uwa*` wrappers that always delegate to the current checkout.

Regression/CI and real macOS validation passed. Detailed record: `docs/CODEX_UWA_LIFECYCLE_LIVE_2026-09-07.md`.

## Versioned provider switch: CLOSED PASS

The former private executable helper `~/.uwa/config_switch.py uwa` was inspected and its contract migrated into `tools/codex_provider_switch.py uwa`.

The normal `codex-uwa` wrapper now uses only repository-managed provider/lifecycle/memory tooling and no longer references the private helper.

Security hardening CI #289 completed successfully. The real macOS validation then proved:

```text
PRIVATE_HELPER_REFERENCE=NO
UNRELATED_CONFIG_PRESERVED=YES
UWA_ROOT_CONTRACT=PASS
UWA_PROVIDER_CONTRACT=PASS
MODEL_SPECIFIC_OVERRIDES_CLEARED=YES
RESTORE_STATE=PRESENT
OLD_PID=67555
NEW_PID=29522
LISTENER_REPLACED=YES
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
VERSIONED_PROVIDER_SWITCH_LIVE_PASS
```

Operator-script caveat: the local venv lacked pytest, so the focused local pytest command did not execute even though a later unconditional echo printed `FOCUSED_TESTS=PASS`. That echo is ignored. Regression evidence comes from successful CI #289; live provider/restart/health evidence comes from the macOS run.

Detailed record: `docs/CODEX_UWA_PROVIDER_SWITCH_MIGRATION_2026-09-08.md`.

## WebCodex architecture review

`yyjeqhc/webcodex` was reviewed at upstream commit `5a4da8fff7a7dc52bd963e8dc22ef530160f28` as an Apache-2.0 reference. Official Codex remains the local executor; WebCodex's Server/Runner execution layer is not copied.

High-value reliability lessons incorporated into later acceptance design include request-loss versus execution-loss separation, uncertain-effect reconciliation before retry, stable identity versus process/browser generation, bounded diagnostics, fail-closed capability compatibility and distinct concurrency planes.

Detailed audit: `docs/WEBCODEX_ARCHITECTURE_REVIEW_2026-09-07.md`.

## Current gate: P1.2 large-context compaction / recovery

P1.2 is now current.

The test must exercise conversation context growth and native Codex compaction/recovery, not just reading a large file. The current design direction is:

```text
seed synthetic token in conversation only
→ same Codex thread
→ deterministic multi-turn large filler with token absent
→ machine-auditable compact-route evidence when available
→ final turn recovers original token without restating it
→ writes exact token bytes to result file
→ reads them back
→ fixed LARGE_CONTEXT_PASS marker
→ independent checker
```

Important classification rule: byte volume plus successful recovery proves large-context stress/recovery. Actual compaction is only claimed when the run has explicit route/lifecycle evidence that `/v1/responses/compact` was used.

## Current gate

```text
Stage A-F protocol/CLI acceptance          PASS
aggregate A-F checker                      PASS
P1.1 compact endpoint + live protocol      PASS
versioned lifecycle implementation/live     PASS
versioned provider switch implementation    PASS
versioned provider switch macOS live        PASS
P1.2 large-context compaction/recovery      CURRENT
P1.3 affinity/restart/uncertain-effect       pending / expanded by WebCodex review
Desktop UI live gate D1-D5                  pending / mandatory before main
```

## Production-hardening roadmap

```text
P1.2 native Codex large-context compaction / stress / recovery
P1.3 lost-affinity / restart + identity fencing + uncertain-effect recovery
Desktop D1-D5 actual UI acceptance
P1.4 real-project long-task pilot
P2 per-continuation serialization / queue planes / controlled-tab stale-result hardening
P3 MCP/plugin namespace + capability fidelity + multi-agent/tool fan-out
P4 successful Responses SSE slimming + bounded trace/transcript hygiene
P5 runtime/build identity + compatibility preflight + final regression/release checklist
```

## Recording discipline

Every live result, failure, repair and disruptive checkpoint must be committed before the next step. README, canonical current state, this file, stage/failure records and Draft PR must stay aligned.

## Final merge plan

Merge `codex-web-bridge-v2` into `main` only after compact/large-context/restart hardening, actual Desktop UI acceptance, the real-project pilot, final regression, CI and repository-safety checks are green and the handoff documentation is current.
