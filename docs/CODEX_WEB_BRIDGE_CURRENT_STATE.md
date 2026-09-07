# Codex Web Bridge current state

Canonical handoff for `codex-web-bridge-v2`.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while routing model inference through UWA to logged-in ChatGPT Web. Codex remains authoritative for filesystem, shell, edits, tests, Git, sandbox and approval. CLI/protocol acceptance is necessary but does not replace the mandatory Desktop UI gate.

## Verified live acceptance

```text
Stage A-F protocol/CLI acceptance                 PASS
aggregate A-F checker                             PASS
Responses tool / call-id continuity               PASS
P1.1 Responses compact direct live                PASS
versioned UWA lifecycle/provider switch CI/live   PASS
P1.2 stream/usage compatibility                   PASS
P1.2 rollout TokenCount persistence               PASS
P1.2 attempt-2 threshold diagnosis                PASS
P1.2 small-step trigger implementation/CI #340    PASS
P1.2 native auto-compact trigger macOS live       PASS
Codex Desktop UI live gate                        REQUIRED / pending
```

## P1.2 history

Attempt 1 exposed two transport gaps: comment-only SSE keepalive did not reset Codex's idle timer, and zero Responses usage prevented native auto-compact accounting. Both were repaired and validated by CI plus a real non-zero-usage macOS smoke.

Attempt 2 used fixed 20KB filler. The private rollout preserved `TokenCount`, but the last successful active context ended at `55,632`. Exact Codex 0.153.4 source showed the native auto-compact threshold is `57,600`, the separate hard effective cap is `60,800`, and pre-turn compaction runs before the new user message is recorded. The fixed 20KB next turn therefore jumped across the threshold after the compact check. This attempt is classified as an acceptance-runner threshold-crossing defect rather than a broken Codex trigger.

## Native auto-compact trigger: PASS

A dedicated versioned probe approached the threshold correctly. Safe live evidence:

```text
active last tokens
14205
21122
28039
34956
41873
48790
55707
56568
57429
58290
```

Decisive transition:

```text
57429 < 57600
58290 > 57600
PRE_TRIGGER_OVER_HARD_CAP=NO
PRE_TRIGGER_ROLLOUT_COMPACT_MARKERS=0
```

The following tiny turn produced:

```text
TRIGGER_REPLY_EXACT=YES
TRIGGER_TOOL_EFFECTS=0
ROLLOUT_COMPACT_MARKER_DELTA=1
REMOTE_COMPACT_ROUTE_DELTA=0
REMOTE_COMPACT_SUCCESS_DELTA=0
TOKEN_LEAK_WORKSPACE=NO
AUTO_COMPACT_MODE=LOCAL_FALLBACK
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

This proves the Codex 0.153.4 threshold trigger, TokenCount persistence/resume restoration and local fallback path are healthy under UWA.

Detailed live record: `docs/CODEX_P1_AUTO_COMPACT_TRIGGER_LIVE_PASS_2026-09-08.md`.

## Current gate: remote compaction capability

P1.1 already proves UWA's `POST /v1/responses/compact` endpoint directly works. The remaining P1.2 compatibility blocker is that Codex 0.153.4 classifies the normal `Universal Web API` custom provider as `RemoteCompactionSupport::Unsupported`, so native auto-compact chooses local fallback instead of the remote endpoint.

Do not blindly rename the provider to `OpenAI`. The next gate is exact-release capability analysis: identify the narrowest safe way to enable remote compaction without enabling unrelated provider-specific behavior. Inspect the provider classifier and all relevant Azure/provider-name branches first; then implement regression coverage before live validation.

## Current status

```text
P1.1 compact endpoint + direct live                PASS
versioned lifecycle/provider switch                PASS
P1.2 stream/usage compatibility                    PASS
P1.2 TokenCount persistence                        PASS
P1.2 native auto-compact trigger/local fallback    PASS
P1.2 remote compact capability                     CURRENT
P1.3 lost-affinity/restart + identity fencing      pending
Desktop UI D1-D5                                   pending / mandatory
```

## Production-hardening order

```text
P1.2 remote compact capability + compact/recovery proof
P1.3 lost-affinity / restart + identity fencing + uncertain-effect recovery
Desktop UI live acceptance D1-D5
P1.4 real-project long-task pilot
P2 per-continuation serialization / queue planes / controlled-tab stale-result hardening
P3 MCP/plugin namespace, capability fidelity and multi-agent/tool fan-out
P4 Responses SSE slimming, bounded trace and transcript hygiene
P5 runtime/build identity, compatibility preflight, final regression and release checklist
```

## Continuity layers

1. Codex Desktop / CLI thread history.
2. Private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Git-tracked handoff documents as long-term project truth.

## Collaboration and merge policy

Every completed stage, important failure, repair and disruptive checkpoint is committed before moving on. README, this canonical state, progress tracking, stage/failure records and Draft PR stay aligned.

Do not merge into `main` until P1 hardening, Desktop D1-D5, the real-project pilot, final regression, CI, docs and public-repository safety checks are green.

## Public repository safety

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, Codex memory workspace content, or private project source captured during acceptance.
