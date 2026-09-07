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
Codex Desktop UI live gate                 REQUIRED / pending
```

Stage F crossed a real UWA restart. Process-local affinity was confirmed destroyed (`binding_count=4 -> 0`), then the same Codex thread resumed without repeating the token, executed a real local command, restored `EMBER-7319\n`, returned `CONTEXT_PASS`, and passed the independent checker.

Important evidence boundary: the final Stage E/F runs were machine-audited primarily via `codex exec` / `codex exec resume`. They prove the Responses/thread/local-tool/restart chain, but they do not close the Desktop UI gate. The additional cases are defined in `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`.

## Aggregate A-F regression incident: CLOSED

The first post-Stage-F aggregate run hit a Stage C harness false failure caused by unrelated `PROMPTS.md`, `__pycache__` and `.pyc` artifacts. The checker was narrowed to tracked diffs under `git_diff/`, regression coverage was added, and the unchanged existing workspace then passed every scenario plus `ACCEPTANCE_PASS`.

## P1.1 compact protocol: PASS

P1.1 implemented `POST /v1/responses/compact`. The first live HTTP 500 was traced to an incompatible stdlib-style logger call. That defect and the equivalent warning branch were repaired with single-argument preformatted messages plus route-level regressions. Security hardening CI #239 for repair code commit `7c6d7ff` passed.

A later rerun still returned the old logger signature error even though the repaired source and fresh interpreter bytecode were correct. Listener inspection proved the reason: TCP 8199 was still served by an old process that predated the repair. The normal stop/start workflow had reported success without replacing the real listener.

The operator then terminated the verified repository listener, proved TCP 8199 was empty, started UWA again, required a different listener PID, confirmed `/health`, and reran the unchanged compact probe. Final live evidence:

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

P1.1 is therefore closed as PASS. The stale-runtime incident is not a second compact-handler defect; it is a separate UWA process-lifecycle defect that must be hardened before restart-heavy P1.2/P1.3 testing.

Current status:

```text
P1.1 compact endpoint implementation        PASS
P1.1 route-level regressions                PASS
P1.1 repair CI                              PASS
P1.1 fresh-listener macOS direct probe      PASS: HTTP 200
UWA stop/start listener lifecycle           CURRENT
P1.2 large-context compaction/recovery      NEXT after lifecycle hardening
P1.3 lost-affinity/restart fallback         pending
Desktop UI D1-D5                            pending / mandatory before main
```

Detailed records:

- `docs/CODEX_P1_RESPONSES_COMPACT_GAP_2026-09-07.md`
- `docs/CODEX_P1_COMPACT_LIVE_500_2026-09-07.md`
- `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`

## Official-account escape hatch: automated

`python3 tools/codex_provider_switch.py official` is now designed as a one-command macOS switch. It automatically quits ChatGPT Desktop/Codex, stops the verified UWA TCP 8199 listener only when its cwd matches this checkout, restores the saved Codex Memories settings, removes only top-level provider/model/reasoning pins, preserves authentication and the `[model_providers.uwa]` definition, then reopens ChatGPT Desktop. No model or reasoning level is hard-coded.

The script fails closed if it cannot prove the listener belongs to this repository or cannot reopen a supported Desktop application. Manual quit/reopen is fallback only, not the normal documented workflow.

## Continuity layers

1. Codex Desktop / CLI thread history.
2. Private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Git tracked handoff documents as long-term project truth.

## Production-hardening order

```text
P1 harden real UWA stop/start listener lifecycle
P1 large-context compaction / stress / recovery
P1 lost-affinity / restart fallback deeper validation
Desktop UI live acceptance D1-D5
P1 real-project long-task pilot
P2 concurrent request / queue / controlled-tab hardening
P3 MCP/plugin namespace and multi-agent/tool fan-out
P4 Responses SSE slimming and transcript hygiene
P5 final regression, operator docs and release checklist
```

## Collaboration rule

Every completed stage, important failure, repair and disruptive checkpoint is committed before moving on. README, this canonical state, progress tracking, stage/failure records and Draft PR should remain aligned.

## Merge policy

Do not merge into `main` yet. Merge only after compact/large-context/restart hardening, the Desktop UI gate, real-project pilot, final regression, CI, documentation and public-repository safety checks are green.

## Public repository safety

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, Codex memory workspace content, or private project source captured during acceptance.
