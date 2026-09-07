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
P1.1 Responses compact direct live           PASS
```

Evidence note: the final Stage E/F runs were audited primarily through `codex exec` / `codex exec resume`. They close the protocol/CLI continuity gate but do not close actual ChatGPT Desktop UI acceptance. A mandatory Desktop D1-D5 gate is tracked in `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`.

## Aggregate checker false failure: CLOSED

The repaired full checker in the existing workspace passed every scenario plus `ACCEPTANCE_PASS`.

## P1 compact protocol: CLOSED PASS

P1.0 confirmed `/v1/responses/compact` was initially absent. P1.1 implemented the route.

The first live HTTP 500 was traced to stdlib-style multi-argument logging against UWA's one-argument `SecureLogger`. The narrow repair changed success/error logging to single preformatted messages and added route-level one-argument logger regressions. Security hardening CI #239 for repair code commit `7c6d7ff` passed.

The apparent post-repair recurrence was ultimately proven to be stale runtime state: the real TCP 8199 listener predated the repair even though the checkout and fresh interpreter contained the corrected bytecode.

After terminating the verified repository listener, proving TCP 8199 empty, starting a different UWA PID and rerunning the unchanged probe, the real macOS runtime returned:

```text
PORT_8199_EMPTY=YES
LISTENER_REPLACED=YES
COMPACT_HTTP_CODE=200
JSON_PARSE=PASS
OUTPUT_IS_LIST=YES
OUTPUT_COUNT=1
OUTPUT_0_TYPE=message ROLE=assistant
MARKER_PRESERVED=YES
TASK_PRESERVED=YES
```

P1.1 is therefore PASS.

Detailed records:

- `docs/CODEX_P1_RESPONSES_COMPACT_GAP_2026-09-07.md`
- `docs/CODEX_P1_COMPACT_LIVE_500_2026-09-07.md`

## Official Codex Desktop recovery: automated

`tools/codex_provider_switch.py official` now performs the normal macOS official-account switch as one automated operation: quit Desktop, stop only the verified repository UWA listener, restore saved Memories settings, remove top-level provider/model/reasoning pins, preserve authentication/UWA provider definition, and reopen Desktop. The normal workflow no longer requires manual quit/reopen.

## Lifecycle discovery

The macOS acceptance machine resolved both lifecycle commands to standalone local executables:

```text
codex-uwa-stop -> /Users/jerson/bin/codex-uwa-stop
codex-uwa      -> /Users/jerson/bin/codex-uwa
```

They are not shell functions or aliases, and no related definition was found in the inspected shell startup files. Repository search also found no canonical source/install definition for these scripts. The stop/start implementation is therefore currently local untracked state and cannot be covered by CI.

The current repair target is to inspect these scripts, migrate their authoritative logic into repository-tracked tooling, add ownership-aware listener stop plus fresh-PID/health verification and regression coverage, and reduce the local `~/bin` commands to wrappers/symlinks.

## Current gate

```text
Stage A-F protocol/CLI acceptance          PASS
aggregate A-F checker                      PASS
P1.1 compact endpoint + live protocol      PASS
UWA real listener stop/start lifecycle     CURRENT
lifecycle implementation in repository     MISSING
P1.2 large-context compaction/recovery     NEXT
P1.3 lost-affinity/restart fallback        pending
Desktop UI live gate D1-D5                 pending / mandatory before main
```

## Production-hardening roadmap

```text
P1.1 migrate/harden UWA stop/start lifecycle into tracked code
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
