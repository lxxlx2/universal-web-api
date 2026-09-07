# Codex Web Bridge current state

Canonical handoff for `codex-web-bridge-v2`.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while routing model inference through UWA to logged-in ChatGPT Web. Codex remains authoritative for filesystem, shell, edits, tests, Git, sandbox and approval.

The production target explicitly includes normal use from ChatGPT Desktop in Codex mode. CLI/protocol acceptance remains necessary evidence, but it is not sufficient proof of Desktop UI compatibility.

## Verified live acceptance

```text
Stage A-F protocol/CLI acceptance          PASS
aggregate A-F checker                      PASS
Responses tool / call-id continuity        PASS
P1.1 Responses compact direct live         PASS
versioned UWA lifecycle CI/live            PASS
versioned UWA provider switch CI/live      PASS
P1.2 stream compatibility CI #313          PASS
P1.2 non-zero usage macOS smoke            PASS
P1.2 rollout TokenCount persistence        PASS
P1.2 second full large-context run         FAIL / runner threshold defect identified
Codex Desktop UI live gate                 REQUIRED / pending
```

## P1.1 compact protocol: PASS

`POST /v1/responses/compact` is implemented and direct macOS validation returned HTTP 200 with valid compact output after the stale-listener incident was repaired.

## Versioned lifecycle/provider switch: PASS

UWA lifecycle, provider switching and Memories handling are repository-managed. The normal `codex-uwa` path no longer executes `~/.uwa/config_switch.py`. Real macOS validation proved listener replacement, provider contract preservation, restore state and healthy UWA/browser state.

## Current gate: P1.2 native Codex large-context compaction / recovery

### Attempt 1

The first full macOS run completed the seed plus seven filler turns, then round 8 failed with an SSE idle timeout. Successful turns also exposed all-zero Responses usage.

Repairs:

1. comment-only heartbeat -> real `response.in_progress` SSE event;
2. bounded fallback token usage when real non-zero usage is unavailable;
3. failed-turn evidence preservation.

Security hardening CI #313 passed. A real macOS smoke then proved non-zero usage reaches Codex.

### Attempt 2

The repaired run produced growing CLI cumulative usage:

```text
21230 -> 42219 -> 70125 -> 104948 -> 146688 -> 195345 -> 250919
```

Rounds 1-7 returned exact filler ACKs with zero tool effects, but `/v1/responses/compact` route/success counters remained zero. Round 8 failed the filler contract.

### Catalog/config/rollout diagnosis

Read-only live inspection proved:

```text
installed Codex                  0.153.4
cached chatgpt context window    64000
live UWA context window          64000
catalog auto-compact field       null
persisted TokenCount events      9
persisted model context window   60800
model_context_window override    none
model_auto_compact override      none
```

The actual rollout preserved token usage across resume. Safe `last_tokens` values progressed:

```text
7213 -> 14130 -> 21047 -> 27964 -> 34881 -> 41798 -> 48715 -> 55632
```

So stale catalog, missing TokenCount persistence, and resume token-loss are closed hypotheses.

### Exact Codex 0.153.4 behavior

The installed release was checked against upstream tag `rust-v0.153.4`, commit `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`.

Confirmed facts:

1. `context_window_token_status()` uses active-context usage derived from `last_token_usage.total_tokens` plus any items added after the last model-generated item; it does not use lifetime cumulative `total_token_usage.total_tokens` as the active context size.
2. `ModelInfo::auto_compact_token_limit()` derives `90%` of the resolved context window when the explicit field is absent, so the native auto-compact threshold is `57,600`.
3. The separate hard effective full-context cap is `64,000 * 95% = 60,800`.
4. Round 7 therefore ended at about `55,632`, only 1,968 tokens below auto-compact and still below the hard cap.
5. `run_turn()` executes pre-turn compaction before context updates and before the new user message are recorded. The exact release source contains a TODO noting that pending incoming items are not yet estimated for this decision.
6. The old runner then injected another 20KB filler after that pre-turn check, allowing round 8 to jump across the 57,600 trigger and toward the hard context boundary before a later turn could observe an already-over-limit previous context.

Therefore attempt 2 is now classified primarily as an acceptance-runner threshold-crossing defect. It is not evidence that Codex failed to run a pre-turn compact after observing an already-over-limit active context.

A separate provider-capability fact remains: the UWA custom provider is `RemoteCompactionSupport::Unsupported` in Codex 0.153.4, so a genuine auto-compact trigger should currently select the local fallback path rather than remote `/v1/responses/compact`.

### Next live gate

Do not change provider identity yet. Use coarse filler until active context is near 57,600, then switch to ~2KB fine filler so one successful response finishes only slightly above 57,600. The following turn must be tiny, allowing Codex's next pre-turn check to observe the over-limit persisted state and exercise auto-compaction deterministically.

This probe will distinguish:

```text
threshold trigger works -> local fallback observed under current provider
threshold trigger still absent -> investigate Codex trigger/persistence mismatch
```

Only after the trigger is proven should the project introduce or reject a narrow remote-compaction capability shim.

Detailed records:

- `docs/CODEX_P1_LARGE_CONTEXT_ACCEPTANCE_2026-09-08.md`
- `docs/CODEX_P1_LARGE_CONTEXT_LIVE_FAILURE_2026-09-08.md`
- `docs/CODEX_P1_LARGE_CONTEXT_SECOND_LIVE_FAILURE_2026-09-08.md`
- `docs/CODEX_P1_STREAM_COMPAT_REPAIR_2026-09-08.md`
- `docs/CODEX_P1_STREAM_USAGE_LIVE_SMOKE_2026-09-08.md`
- `docs/CODEX_P1_MODEL_CACHE_RESUME_DIAG_2026-09-08.md`

## Current status

```text
P1.1 compact endpoint + direct live             PASS
versioned lifecycle/provider switch             PASS
P1.2 stream/usage compatibility CI/live         PASS
P1.2 rollout TokenCount persistence             PASS
P1.2 attempt-2 root cause                       runner threshold-crossing defect
P1.2 small-step auto-compact trigger probe      CURRENT
P1.3 lost-affinity/restart fallback             pending / expanded
Desktop UI D1-D5                                pending / mandatory before main
```

## WebCodex design review

`yyjeqhc/webcodex` remains an Apache-2.0 design reference. Official Codex stays the local execution authority. Reliability lessons incorporated into later gates include uncertain-effect reconciliation, separate identity domains, generation fencing, bounded diagnostics and distinct concurrency planes.

## Continuity layers

1. Codex Desktop / CLI thread history.
2. Private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Git-tracked handoff documents as long-term project truth.

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

Do not merge into `main` yet. Merge only after P1 hardening, Desktop UI acceptance, the real-project pilot, final regression, CI, documentation and public-repository safety checks are green.

## Public repository safety

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, Codex memory workspace content, or private project source captured during acceptance.
