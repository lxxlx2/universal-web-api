# Codex Web Bridge current state

Canonical handoff for `codex-web-bridge-v2`.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while routing model inference through UWA to logged-in ChatGPT Web. Codex remains authoritative for filesystem, shell, edits, tests, Git, sandbox and approval.

The production target explicitly includes normal use from ChatGPT Desktop in Codex mode. CLI/protocol acceptance remains necessary evidence, but it is not sufficient proof of Desktop UI compatibility.

## Verified live acceptance

```text
single-file coding loop                    PASS
Stage A multi-file read/edit/test          PASS
Stage B failure recovery                   PASS
Stage C Git diff discipline                PASS
Stage D long process + write_stdin         PASS
Stage E same-thread context                PASS
Stage F Codex + UWA restart continuity     PASS
aggregate A-F checker                      PASS
real exec_command / native cwd             PASS
Responses tool round trip                  PASS
required-tool enforcement                  PASS
call-id / web-session continuation         PASS
P1.1 Responses compact live                PASS
versioned UWA lifecycle CI                 PASS
versioned UWA lifecycle live               PASS
versioned UWA provider switch CI           PASS
versioned UWA provider switch live         PASS
Codex Desktop UI live gate                 REQUIRED / pending
```

Stage F crossed a real UWA restart. Process-local affinity was confirmed destroyed (`binding_count=4 -> 0`), then the same Codex thread resumed without repeating the token, executed a real local command, restored `EMBER-7319\n`, returned `CONTEXT_PASS`, and passed the independent checker.

Important evidence boundary: the final Stage E/F runs were machine-audited primarily via `codex exec` / `codex exec resume`. They prove the Responses/thread/local-tool/restart chain, but they do not close the Desktop UI gate. The additional cases are defined in `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`.

## Aggregate A-F regression incident: CLOSED

The first post-Stage-F aggregate run hit a Stage C harness false failure caused by unrelated `PROMPTS.md`, `__pycache__` and `.pyc` artifacts. The checker was narrowed to tracked diffs under `git_diff/`, regression coverage was added, and the unchanged existing workspace then passed every scenario plus `ACCEPTANCE_PASS`.

## P1.1 compact protocol: PASS

P1.1 implemented `POST /v1/responses/compact`. The first live HTTP 500 was traced to an incompatible stdlib-style logger call. That defect and the equivalent warning branch were repaired with single-argument preformatted messages plus route-level regressions. Security hardening CI #239 passed.

A later rerun still returned the old logger signature error because TCP 8199 was still served by a process that predated the repair. After verifying listener ownership, clearing the port, starting a different UWA PID and rerunning the unchanged compact probe, the direct macOS runtime returned HTTP 200 with valid assistant `output` while preserving both the marker and task semantics.

P1.1 compact is closed as PASS.

## Versioned UWA lifecycle: PASS

The old local lifecycle scripts had two defects:

1. stop sent TERM and reported success without proving TCP 8199 was empty;
2. start reused any already-healthy listener, so `git pull` could leave stale loaded bytecode active.

The authoritative implementation is repository-tracked in `tools/codex_uwa_lifecycle.py`, with thin user commands installed by `tools/install_codex_uwa_commands.py`.

Real macOS evidence included a clean stop, a different listener PID, matching repository cwd, healthy service and connected browser. Detailed record: `docs/CODEX_UWA_LIFECYCLE_LIVE_2026-09-07.md`.

## Versioned UWA provider switch: PASS

The former private helper `~/.uwa/config_switch.py uwa` was inspected and its UWA contract migrated into `tools/codex_provider_switch.py uwa`.

The installed `codex-uwa` wrapper now depends only on repository-managed logic:

```text
codex_uwa_memory_guard.py disable
codex_provider_switch.py uwa
codex_uwa_lifecycle.py restart
```

Real macOS validation proved:

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

Security hardening CI #289 completed successfully for the provider/wrapper implementation.

One operator-script caveat is recorded explicitly: local focused pytest did not execute because the local venv lacked pytest, while an unconditional echo printed `FOCUSED_TESTS=PASS`. That line is not counted as test evidence. CI #289 supplies regression evidence; the live macOS run supplies real configuration/restart/health evidence.

Detailed record: `docs/CODEX_UWA_PROVIDER_SWITCH_MIGRATION_2026-09-08.md`.

## Current gate: P1.2 native Codex large-context compaction / recovery

The final known Git-external executable dependency in the normal UWA entry path is closed. The current gate is now a synthetic, machine-auditable long-context test that exercises native Codex continuation and `/v1/responses/compact` behavior rather than merely proving that a large file can be read.

P1.2 must distinguish:

- large-context stress from actual compaction evidence;
- conversation-memory recovery from local-file memory;
- native Codex thread continuity from UWA web-session affinity;
- exact success from prose-only claims.

The intended acceptance shape is:

1. seed a synthetic token only in the conversation;
2. send deterministic large filler across the same Codex thread without repeating the token;
3. gather machine-auditable evidence that the compact route was used if available;
4. final turn must recover the token without the user restating it, write exact bytes to a result file, read them back and return a fixed pass marker;
5. independent checker verifies exact bytes and required evidence.

If explicit compaction evidence cannot be proven, classify the run as large-context stress/recovery rather than claiming compaction PASS.

Current status:

```text
P1.1 compact endpoint + direct live         PASS
versioned lifecycle implementation/live     PASS
versioned provider switch implementation    PASS
versioned provider switch macOS live        PASS
P1.2 large-context compaction/recovery      CURRENT
P1.3 lost-affinity/restart fallback         pending / expanded
Desktop UI D1-D5                            pending / mandatory before main
```

## Official-account escape hatch: automated

`python3 tools/codex_provider_switch.py official` is a one-command macOS switch. It automatically quits ChatGPT Desktop/Codex, stops the verified UWA TCP 8199 listener only when its cwd matches this checkout, restores saved Codex Memories settings, removes top-level provider/model/reasoning pins, preserves authentication, and reopens ChatGPT Desktop. No account model or reasoning level is hard-coded in official mode.

## WebCodex design review

`yyjeqhc/webcodex` was reviewed at upstream commit `5a4da8fff7a7a7dc52bd963e8dc22ef530160f28` as an Apache-2.0 design reference. It does not replace the V2 architecture: official Codex remains the local filesystem/shell/Git/sandbox/approval owner.

Useful reliability lessons incorporated into later gates include request-loss versus execution-loss separation, uncertain-effect reconciliation before retry, stable identity versus process/browser generation fencing, fail-closed capability compatibility, bounded diagnostics and distinct concurrency planes.

Detailed audit: `docs/WEBCODEX_ARCHITECTURE_REVIEW_2026-09-07.md`.

## Continuity layers

1. Codex Desktop / CLI thread history.
2. Private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Git tracked handoff documents as long-term project truth.

P1.3 will formalize the identity boundary further: Codex thread, Responses `response_id`, tool `call_id`, ChatGPT `/c/...` affinity, UWA process generation, controlled-tab generation and Codex-owned local process state are separate domains and must never be inferred from one another.

## Production-hardening order

```text
P1.2 native Codex large-context compaction / stress / recovery
P1.3 lost-affinity / restart + identity fencing + uncertain-effect recovery
Desktop UI live acceptance D1-D5
P1.4 real-project long-task pilot
P2 per-continuation serialization / queue planes / controlled-tab stale-result hardening
P3 MCP/plugin namespace, capability fidelity and multi-agent/tool fan-out
P4 Responses SSE slimming, bounded trace and transcript hygiene
P5 runtime/build identity, compatibility preflight, final regression and release checklist
```

## Collaboration rule

Every completed stage, important failure, repair and disruptive checkpoint is committed before moving on. README, this canonical state, progress tracking, stage/failure records and Draft PR should remain aligned.

## Merge policy

Do not merge into `main` yet. Merge only after compact/large-context/restart hardening, the Desktop UI gate, real-project pilot, final regression, CI, documentation and public-repository safety checks are green.

## Public repository safety

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, Codex memory workspace content, or private project source captured during acceptance.
