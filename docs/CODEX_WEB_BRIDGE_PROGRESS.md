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
versioned UWA lifecycle CI                  PASS: #269
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

## Official Codex Desktop recovery: automated

`tools/codex_provider_switch.py official` performs the normal macOS official-account switch as one automated operation: quit Desktop, stop only the verified repository UWA listener, restore saved Memories settings, remove top-level provider/model/reasoning pins, preserve authentication/UWA provider definition, and reopen Desktop. The normal workflow no longer requires manual quit/reopen.

## UWA lifecycle hardening

Inspection of the real macOS lifecycle scripts confirmed two defects:

1. the old `codex-uwa-stop` did not prove TCP 8199 was empty after TERM and had no required escalation path;
2. the old `codex-uwa` reused a healthy listener rather than requiring a fresh process, allowing stale bytecode after repository updates.

The authoritative lifecycle has now moved into repository-tracked code:

- `tools/codex_uwa_lifecycle.py` performs ownership-aware listener discovery, TERM/wait/KILL, port-empty proof, fresh start, replacement proof and `/health` verification;
- `tools/install_codex_uwa_commands.py` installs thin `~/bin/codex-uwa*` wrappers that delegate to the current checkout;
- UWA startup automatically disables Codex Memories;
- tests cover fail-closed foreign listeners, TERM->KILL escalation, required stop/start ordering, PID replacement and wrapper delegation;
- Security hardening CI #269 completed successfully, including upstream regression.

The remaining lifecycle gate is a real macOS install + stop/start run on the acceptance machine.

One transitional Git-external helper remains: `~/.uwa/config_switch.py uwa` supplies the current exact UWA provider config contract. After lifecycle live validation, it will be inspected and migrated into Git.

## Current gate

```text
Stage A-F protocol/CLI acceptance          PASS
aggregate A-F checker                      PASS
P1.1 compact endpoint + live protocol      PASS
versioned lifecycle implementation         PASS
versioned lifecycle regression / CI        PASS: #269
versioned lifecycle macOS live             CURRENT
P1.2 large-context compaction/recovery     NEXT
P1.3 lost-affinity/restart fallback        pending
Desktop UI live gate D1-D5                 pending / mandatory before main
```

## Production-hardening roadmap

```text
P1.1 validate versioned UWA lifecycle on macOS
P1.1 migrate ~/.uwa/config_switch.py contract into Git
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
