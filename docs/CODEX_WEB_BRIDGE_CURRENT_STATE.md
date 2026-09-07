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

## P1.2 history

Attempt 1 exposed two transport gaps: comment-only SSE keepalive did not reset Codex's idle timer, and zero Responses usage prevented native auto-compact accounting. Both were repaired and validated by CI plus a real non-zero-usage macOS smoke.

Attempt 2 used fixed 20KB filler. The private rollout preserved `TokenCount`, but the last successful active context ended at `55,632`. Exact Codex 0.153.4 source showed the native auto-compact threshold is `57,600`, the separate hard effective cap is `60,800`, and pre-turn compaction runs before the new user message is recorded. The fixed 20KB next turn therefore jumped across the threshold after the compact check. This attempt is classified as an acceptance-runner threshold-crossing defect rather than a broken Codex trigger.

## Native auto-compact trigger: PASS

The dedicated small-step probe crossed the threshold safely:

```text
57429 < 57600
58290 > 57600
PRE_TRIGGER_OVER_HARD_CAP=NO
PRE_TRIGGER_ROLLOUT_COMPACT_MARKERS=0
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

## Remote compaction capability audit / implementation

Exact Codex 0.153.4 source shows configured providers get remote compaction V2 only when `is_openai()` or `is_azure_responses_provider(...)` is true.

Using the broad `OpenAI` identity is rejected because `is_openai()` controls unrelated backend behavior. The narrow compatibility choice is the configured UWA provider display name `Azure`, while keeping:

```text
provider id                   uwa
base_url                      http://127.0.0.1:8199/v1
wire_api                      responses
requires_openai_auth          false
supports_websockets           false
is_openai()                   false
remote_compaction             V2
```

Remote V2 still targets the same provider-relative `responses/compact` route. Known side effect: `codex doctor` skips its own `/models` reachability probe for Azure-classified providers; normal runtime models management remains provider-backed.

Versioned fail-closed implementation:

- `tools/codex_remote_compaction_compat.py`
- `tests/test_codex_remote_compaction_compat.py`

The helper changes only the managed UWA provider `name` after verifying the full loopback/auth/wire contract. Security hardening #351 / run `34164070091`, head `127ed09fbb1f8941ff4332db72bf498fb9f80287`, completed `success`.

Detailed audit: `docs/CODEX_P1_REMOTE_COMPACTION_CAPABILITY_AUDIT_2026-09-08.md`.

## Current gate

Real macOS remote-compaction live validation is CURRENT. Apply the versioned compatibility helper to the managed UWA config, verify the safe contract, then rerun the small-step threshold probe.

Required evidence:

```text
THRESHOLD_CROSSED=YES
PRE_TRIGGER_OVER_HARD_CAP=NO
REMOTE_COMPACT_ROUTE_DELTA>=1
REMOTE_COMPACT_SUCCESS_DELTA>=1
ROLLOUT_COMPACT_MARKER_DELTA>=1
AUTO_COMPACT_MODE=REMOTE
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

After that passes, P1.2 still requires same-thread post-remote-compact recovery of the original conversation-only synthetic token through a real local write/read before closure.

## Current status

```text
P1.1 compact endpoint + direct live                PASS
versioned lifecycle/provider switch                PASS
P1.2 stream/usage compatibility                    PASS
P1.2 TokenCount persistence                        PASS
P1.2 native trigger/local fallback                 PASS
P1.2 remote capability shim CI                     PASS
P1.2 native remote compact macOS live              CURRENT
P1.3 lost-affinity/restart + identity fencing      pending
Desktop UI D1-D5                                   pending / mandatory
```

## Production-hardening order

```text
P1.2 native remote compact live + same-thread recovery
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
