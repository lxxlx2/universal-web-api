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
P1.2 native auto-compact trigger/local fallback   PASS
P1.2 remote-capability shim implementation/CI     PASS (#351)
Codex Desktop UI live gate                        REQUIRED / pending
```

## Native auto-compact trigger: PASS

The small-step live probe crossed the native threshold safely and the next tiny turn produced a Codex rollout compaction lifecycle marker:

```text
57429 < 57600
58290 > 57600
PRE_TRIGGER_OVER_HARD_CAP=NO
ROLLOUT_COMPACT_MARKER_DELTA=1
REMOTE_COMPACT_ROUTE_DELTA=0
REMOTE_COMPACT_SUCCESS_DELTA=0
AUTO_COMPACT_MODE=LOCAL_FALLBACK
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

This proves threshold detection, TokenCount persistence/resume restoration and local fallback under Codex 0.153.4.

## Remote capability shim: implementation/CI PASS

Exact Codex 0.153.4 capability audit selected a narrow compatibility identity: only `[model_providers.uwa].name` becomes `Azure`, while provider id, loopback URL, Responses wire API, disabled OpenAI auth and unrelated config remain unchanged.

Tracked helper/test:

- `tools/codex_remote_compaction_compat.py`
- `tests/test_codex_remote_compaction_compat.py`

Security hardening #351 / run `34164070091` passed. Latest aligned documentation/public-safety CI #355 / run `34164304589` also passed.

## Current blocker: remote V2 protocol shape

The real macOS Azure-name shim has NOT been enabled yet because a pre-live exact-release audit found an additional protocol mismatch.

Current UWA P1.1 compact is a legacy unary adapter:

```text
POST /v1/responses/compact
→ HTTP JSON
→ output contains assistant message item(s)
```

Codex 0.153.4 remote V2 requires a streaming Responses contract and accepts the attempt only when exactly one output item is:

```text
type = compaction
encrypted_content = <opaque payload>
```

The V2 collector explicitly fails if it does not receive exactly one `ResponseItem::Compaction`. Therefore enabling the capability shim against the current legacy endpoint would be a predictable live failure.

Detailed blocker record: `docs/CODEX_P1_REMOTE_V2_PROTOCOL_GAP_2026-09-08.md`.

## Current repair gate

Keep P1.1 unary behavior. Add a V2 path for streaming `compaction_trigger` requests that:

1. produces the bounded web-backed summary with tools disabled;
2. wraps it in a UWA-owned opaque/bounded compaction envelope;
3. emits parseable SSE with exactly one `type=compaction` output item and `response.completed`;
4. emits parseable heartbeat events during long web inference;
5. decodes only UWA-owned compaction envelopes back into model-visible compacted context on later normal Codex Responses turns;
6. fails closed on foreign/corrupt envelopes;
7. never logs summary/envelope content.

The schema field is named `encrypted_content`, but UWA must not represent its local envelope as OpenAI encryption.

## Current status

```text
P1.1 legacy compact endpoint/direct live             PASS
P1.2 native threshold/local fallback                 PASS
P1.2 remote capability shim implementation/CI        PASS
P1.2 remote V2 response/envelope protocol repair     CURRENT
P1.2 native remote compact macOS live                BLOCKED on repair
P1.2 same-thread post-remote recovery                 pending
P1.3 lost-affinity/restart + identity fencing         pending
Desktop UI D1-D5                                      pending / mandatory
```

## Production-hardening order

```text
P1.2 remote V2 protocol repair → CI → native remote compact live → same-thread recovery
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

## Collaboration / merge / safety

Every completed stage, important failure, repair and disruptive checkpoint is committed before moving on. README, this canonical state, progress tracking, stage/failure records and Draft PR stay aligned.

Do not merge into `main` until P1 hardening, Desktop D1-D5, the real-project pilot, final regression, CI, docs and public-repository safety checks are green.

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, Codex memory workspace content, or private project source captured during acceptance.
