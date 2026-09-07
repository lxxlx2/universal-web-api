# Codex Web Bridge current state

Canonical handoff for `codex-web-bridge-v2`.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while routing model inference through UWA to logged-in ChatGPT Web. Codex remains authoritative for filesystem, shell, edits, tests, Git, sandbox and approval.

The production target explicitly includes normal use from ChatGPT Desktop in Codex mode. CLI/protocol acceptance remains necessary evidence, but it is no longer treated as sufficient proof of Desktop UI compatibility.

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
Codex Desktop UI live gate                 REQUIRED / pending
```

Stage F crossed a real UWA restart. Process-local affinity was confirmed destroyed (`binding_count=4 -> 0`), then the same Codex thread resumed without repeating the token, executed a real local command, restored `EMBER-7319\n`, returned `CONTEXT_PASS`, and passed the independent checker.

Important evidence boundary: the final Stage E/F runs were machine-audited primarily via `codex exec` / `codex exec resume`. They prove the Responses/thread/local-tool/restart chain, but they do not close the Desktop UI gate. The additional cases are defined in `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`.

## Aggregate A-F regression incident: CLOSED

The first post-Stage-F aggregate run hit a Stage C harness false failure caused by unrelated `PROMPTS.md`, `__pycache__` and `.pyc` artifacts. The checker was narrowed to tracked diffs under `git_diff/`, regression coverage was added, and the unchanged existing workspace then passed:

```text
multi_file: PASS
failure_recovery: PASS
git_diff: PASS
interactive: PASS
context: PASS
ACCEPTANCE_PASS
```

Detailed record: `docs/CODEX_FULL_ACCEPTANCE_HARNESS_FALSE_FAILURE_2026-09-07.md`.

## Current P1 gate: Responses compact protocol

Current upstream Codex remote compaction uses:

```text
POST /v1/responses/compact
```

The compact request carries canonical Responses input plus model/instructions and applicable tool/reasoning/text controls. Codex parses the returned JSON `output` items and exposes context compaction as an observable lifecycle item.

Code inspection found no route, and the real macOS runtime probe confirmed:

```text
COMPACT_ROUTE_REGISTERED=NO
HTTP/1.1 404 Not Found
```

P1.0 is therefore complete. P1.1 is the current implementation gate.

Next sequence:

```text
1. implement minimal compatible /v1/responses/compact endpoint + regression tests
2. CI + direct compact protocol acceptance
3. synthetic large-context workload
4. require observable contextCompaction plus post-compaction recovery
5. lost-affinity / restart fallback deeper validation
6. mandatory Codex Desktop UI D1-D5 live gate
7. real-project long-task pilot
```

Detailed records:

- `docs/CODEX_P1_RESPONSES_COMPACT_GAP_2026-09-07.md`
- `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`

## Official-account escape hatch

The project now includes `tools/codex_provider_switch.py`. `official` removes top-level provider/model/reasoning pins from `~/.codex/config.toml` after creating a backup. It does not modify login credentials and does not select a model. After fully restarting ChatGPT Desktop, the user chooses any model made available by the signed-in ChatGPT account/workspace.

## Continuity layers

1. Codex Desktop / CLI thread history.
2. Private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Git tracked handoff documents as long-term project truth.

## Production-hardening order

```text
P1 compact protocol compatibility
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
