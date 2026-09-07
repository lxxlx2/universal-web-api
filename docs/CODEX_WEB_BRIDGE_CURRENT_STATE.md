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

## Current P1 gate: compact live HTTP 500 diagnosis

Upstream Codex remote compaction uses:

```text
POST /v1/responses/compact
```

Initial code inspection found no route, and the first real macOS runtime probe confirmed:

```text
COMPACT_ROUTE_REGISTERED=NO
HTTP/1.1 404 Not Found
```

P1.1 then implemented and registered the endpoint in `app/api/codex_compact.py`, with regression coverage in `tests/test_codex_responses_compact.py`. GitHub Actions run #220 for implementation/test head `5cccbcf4b7f5f0c53467423ce1e5250c7fc1457d` completed successfully.

The first post-implementation macOS runtime probe then observed:

```text
COMPACT_ROUTE_REGISTERED=YES
COMPACT_HTTP_CODE=500
JSON_PARSE=PASS
OUTPUT_IS_LIST=NO
OUTPUT_COUNT=0
MARKER_PRESERVED=NO
TASK_PRESERVED=NO
```

Therefore route registration and unit/CI coverage are green, but the live handler is still failing. P1.1 is NOT PASS and P1.2 large-context stress remains blocked.

Code inspection narrows the current diagnostic boundary: web-mode preparation and the backing request are already inside an exception block that converts failures to structured `502`; the raw `500` points more strongly to an exception before or after that block, such as request adaptation, payload sanitization, output conversion, or another uncovered route-level path. This is still a hypothesis until the local traceback is inspected.

Next sequence:

```text
1. extract the local compact traceback without publishing private runtime data
2. reproduce the exact failing route-level shape in regression tests
3. implement the narrow repair
4. CI green
5. rerun the same direct compact probe -> HTTP 200 + assistant output
6. synthetic large-context workload
7. observable contextCompaction + post-compaction recovery
8. lost-affinity / restart fallback deeper validation
9. mandatory Codex Desktop UI D1-D5 live gate
10. real-project long-task pilot
```

Detailed records:

- `docs/CODEX_P1_RESPONSES_COMPACT_GAP_2026-09-07.md`
- `docs/CODEX_P1_COMPACT_LIVE_500_2026-09-07.md`
- `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`

## Official-account escape hatch

`tools/codex_provider_switch.py official` backs up `~/.codex/config.toml`, removes only top-level provider/model/reasoning pins, keeps the UWA provider definition, and leaves authentication untouched. After fully restarting ChatGPT Desktop, the signed-in ChatGPT account/workspace controls model availability; no model or reasoning level is hard-coded by the restore procedure.

## Continuity layers

1. Codex Desktop / CLI thread history.
2. Private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Git tracked handoff documents as long-term project truth.

## Production-hardening order

```text
P1 compact live protocol repair / acceptance
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
