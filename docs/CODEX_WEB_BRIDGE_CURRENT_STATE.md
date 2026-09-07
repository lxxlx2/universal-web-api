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

The authoritative implementation is now repository-tracked in `tools/codex_uwa_lifecycle.py`, with thin user commands installed by `tools/install_codex_uwa_commands.py`.

The real macOS live run produced:

```text
OLD_PID=57575
STOPPED_LISTENERS=57575
PORT_EMPTY=YES
PORT_8199_EMPTY=YES
NEW_PID=67555
LISTENER_REPLACED=YES
NEW_CWD=/Users/jerson/universal-web-api
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
VERSIONED_LIFECYCLE_PASS
```

This closes the stale-runtime lifecycle blocker. The normal UWA lifecycle now validates listener ownership, proves the port is empty after stop, requires a different listener on restart, and verifies `/health` plus browser connectivity. UWA startup also automatically disables Codex Memories.

Detailed record: `docs/CODEX_UWA_LIFECYCLE_LIVE_2026-09-07.md`.

## Current gate: migrate final Git-external provider switch

One transitional helper remains in the normal UWA entry path:

```text
~/.uwa/config_switch.py uwa
```

`~/bin/codex-uwa` currently invokes this helper before the repository-managed lifecycle restart. It is now the final known Git-external executable/config mutation path in the normal mode switch.

Current status:

```text
P1.1 compact endpoint + direct live         PASS
versioned lifecycle implementation          PASS
versioned lifecycle regression / CI         PASS
versioned lifecycle macOS live              PASS
UWA provider switch contract in Git         CURRENT / missing
P1.2 large-context compaction/recovery      NEXT after provider migration
P1.3 lost-affinity/restart fallback         pending
Desktop UI D1-D5                            pending / mandatory before main
```

## Official-account escape hatch: automated

`python3 tools/codex_provider_switch.py official` is a one-command macOS switch. It automatically quits ChatGPT Desktop/Codex, stops the verified UWA TCP 8199 listener only when its cwd matches this checkout, restores saved Codex Memories settings, removes only top-level provider/model/reasoning pins, preserves authentication and the `[model_providers.uwa]` definition, then reopens ChatGPT Desktop. No model or reasoning level is hard-coded.

## WebCodex design review

`yyjeqhc/webcodex` was reviewed at upstream commit `5a4da8fff7a7a7dc52bd963e8dc22ef530160f28` as an Apache-2.0 design reference. It does not replace the V2 architecture: WebCodex needs its own local Runner because its cloud MCP clients need an executor, while this project intentionally keeps official Codex Desktop / CLI as the local filesystem/shell/Git/sandbox/approval owner.

The useful lessons are reliability contracts rather than executor code:

- browser/window/transport identity must not become durable task or execution identity;
- request loss is distinct from execution loss;
- uncertain tool effects must be reconciled before any retry;
- stable logical identity and current process/browser generation must remain separate;
- correlation ids and observation cursors are not authority or retry permission;
- protocol capabilities should fail closed when semantics cannot be preserved;
- diagnostics and recovery evidence should remain bounded and secret-free.

Roadmap impact:

- P1.2 stays focused on native Codex `/v1/responses/compact`; durable task state is not a substitute for LLM context compaction.
- P1.3 expands to explicit identity separation, stale-generation fencing and uncertain tool-effect recovery.
- P2 expands per-continuation serialization, distinct concurrency planes and late/stale result rejection.
- P3 uses WebCodex as a primary MCP/schema/capability reference while Codex remains the actual local MCP/tool executor.
- P4/P5 strengthen bounded trace/transcript behavior, build/runtime identity and compatibility diagnostics.

Detailed audit: `docs/WEBCODEX_ARCHITECTURE_REVIEW_2026-09-07.md`.

## Continuity layers

1. Codex Desktop / CLI thread history.
2. Private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Git tracked handoff documents as long-term project truth.

P1.3 will formalize the identity boundary further: Codex thread, Responses `response_id`, tool `call_id`, ChatGPT `/c/...` affinity, UWA process generation, controlled-tab generation and Codex-owned local process state are separate domains and must never be inferred from one another.

## Production-hardening order

```text
P1 migrate ~/.uwa/config_switch.py UWA provider contract into Git
P1 large-context compaction / stress / recovery
P1 lost-affinity / restart + identity fencing + uncertain-effect recovery
Desktop UI live acceptance D1-D5
P1 real-project long-task pilot
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
