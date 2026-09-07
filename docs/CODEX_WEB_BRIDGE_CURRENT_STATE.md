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
P1.2 second full large-context run         FAIL
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

The repaired run produced growing usage:

```text
21230 -> 42219 -> 70125 -> 104948 -> 146688 -> 195345 -> 250919
```

Rounds 1-7 returned exact filler ACKs with zero tool effects, but `/v1/responses/compact` route/success counters remained zero. Round 8 failed the filler contract.

### Model catalog/cache diagnosis

Read-only live inspection proved:

```text
installed Codex                  0.153.4
cached chatgpt context window    64000
live UWA context window          64000
cached truncation limit          57600
live UWA truncation limit        57600
model_context_window override    none
model_auto_compact override      none
visible compact lifecycle 1-7    none
```

Therefore stale catalog, larger cached context, and top-level context/compact overrides are closed hypotheses.

The exact installed Codex release was checked against upstream tag `rust-v0.153.4`, commit `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`.

Two source facts are now established:

1. the custom UWA provider is classified `RemoteCompactionSupport::Unsupported`, because Codex 0.153.4 only enables remote compaction for recognized OpenAI/Azure providers;
2. Codex 0.153.4 already restores token usage on resume/fork from the latest persisted `EventMsg::TokenCount`. Normal `response.completed` handling records token usage, emits `TokenCount`, and ordinary events are persisted into rollout storage.

Therefore a fresh `codex exec resume` process does not inherently discard prior usage. The previous hypothesis that process restart alone explained the missing compact trigger is rejected.

### Current diagnostic boundary

The next fact to establish is whether the actual P1.2 thread rollout contains the expected persisted `TokenCount` events and safe numeric token totals before the later resumed filler turns.

If the rollout has no usable TokenCount state, the usage persistence/restoration chain remains the blocker. If it contains over-threshold usage before a later turn, the fault moves to pre-turn token-limit/compaction selection.

Do not rerun the stress test and do not change provider identity until this is known.

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
P1.2 second full large-context live             FAIL
P1.2 rollout TokenCount persistence diagnosis   CURRENT
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
