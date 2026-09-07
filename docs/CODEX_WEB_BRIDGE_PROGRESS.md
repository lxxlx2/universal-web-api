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

The lifecycle implementation is now repository-tracked in `tools/codex_uwa_lifecycle.py`, while `tools/install_codex_uwa_commands.py` installs thin `~/bin/codex-uwa*` wrappers that always delegate to the current checkout.

Regression/CI passed, then the real macOS validation produced:

```text
STOPPED_LISTENERS=57575
PORT_EMPTY=YES
PORT_8199_EMPTY=YES
OLD_PID=57575
NEW_PID=67555
LISTENER_REPLACED=YES
NEW_CWD=/Users/jerson/universal-web-api
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
VERSIONED_LIFECYCLE_PASS
```

The stale-listener blocker is closed. Detailed record: `docs/CODEX_UWA_LIFECYCLE_LIVE_2026-09-07.md`.

## WebCodex architecture review

`yyjeqhc/webcodex` was reviewed at upstream commit `5a4da8fff7a7a7dc52bd963e8dc22ef530160f28` as an Apache-2.0 reference. The conclusion is to preserve the current V2 architecture: official Codex remains the local executor; WebCodex's Server/Runner execution layer is not copied.

High-value reliability lessons have been incorporated into later acceptance design:

- request loss versus execution loss;
- explicit uncertain-effect reconciliation before retry;
- stable task/correlation identity separated from process/browser generation;
- correlation/observation identifiers never becoming authority or retry permission;
- fail-closed capability compatibility;
- bounded, secret-free recovery diagnostics;
- concurrency planes kept distinct.

Detailed audit: `docs/WEBCODEX_ARCHITECTURE_REVIEW_2026-09-07.md`.

## Current gate: migrate remaining provider switch helper

One transitional Git-external helper remains:

```text
~/.uwa/config_switch.py uwa
```

The current `codex-uwa` thin wrapper still calls it to mutate the Codex UWA provider settings before the versioned restart. The next step is to inspect that helper's exact UWA contract, implement the equivalent operation in repository-tracked tooling, add regression coverage, remove the private-helper dependency, validate the fully versioned switch once, and then begin P1.2.

## Current gate

```text
Stage A-F protocol/CLI acceptance          PASS
aggregate A-F checker                      PASS
P1.1 compact endpoint + live protocol      PASS
versioned lifecycle implementation         PASS
versioned lifecycle regression / CI        PASS
versioned lifecycle macOS live             PASS
UWA provider switch contract in repository CURRENT
P1.2 large-context compaction/recovery     NEXT
P1.3 affinity/restart/uncertain-effect      pending / expanded by WebCodex review
Desktop UI live gate D1-D5                 pending / mandatory before main
```

## Production-hardening roadmap

```text
P1.1 migrate ~/.uwa/config_switch.py UWA contract into Git
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
