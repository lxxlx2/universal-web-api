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

## Current P1 gate: second compact traceback

Upstream Codex remote compaction uses:

```text
POST /v1/responses/compact
```

The initial code/runtime gap was confirmed by `COMPACT_ROUTE_REGISTERED=NO` and HTTP 404. P1.1 then added the route and helper regressions.

The first post-implementation macOS probe reached the route but returned HTTP 500. The first traceback proved the compact backing request and assistant replacement output had already succeeded; the failure occurred on the final success log:

```text
TypeError: SecureLogger.info() takes 2 positional arguments but 3 were given
```

That logger incompatibility and the equivalent latent warning branch were repaired with single-argument preformatted messages. Route-level one-argument logger regressions were added. Security hardening CI #239 for repair code commit `7c6d7ff` completed with `success`.

The operator then pulled through `b3f37ac`, verified the repaired logger line locally, restarted UWA, confirmed `/health` and compact route registration, and reran the exact same direct compact probe. The result remained:

```text
COMPACT_ROUTE_REGISTERED=YES
COMPACT_HTTP_CODE=500
JSON_PARSE=PASS
OUTPUT_IS_LIST=NO
OUTPUT_COUNT=0
MARKER_PRESERVED=NO
TASK_PRESERVED=NO
```

This second live result establishes that the first logger defect is fixed and deployed, while another unhandled runtime path still exists. The second root cause is intentionally unclassified until a fresh post-repair traceback is inspected.

Current status:

```text
route registration                         PASS
first live 500 root cause                  CONFIRMED: SecureLogger signature
first repair + route regressions           DONE
first repair CI                            PASS: #239
post-repair service restart                PASS
post-repair route registration             PASS
post-repair direct compact request         FAIL: HTTP 500
second traceback / root cause              CURRENT / UNKNOWN
P1.2 large-context                         BLOCKED until live compact PASS
Desktop UI D1-D5                           pending / mandatory before main
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
P1 capture second compact traceback and repair exact path
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
