# Codex Web Bridge current state

Canonical handoff for `codex-web-bridge-v2`.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while routing model inference through UWA to logged-in ChatGPT Web. Codex remains authoritative for filesystem, shell, edits, tests, Git, sandbox and approval. CLI/protocol acceptance is necessary but does not replace the mandatory Desktop UI gate.

## Verified acceptance / CI

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
P1.2 remote V2 protocol implementation/CI         PASS (#380)
Codex Desktop UI live gate                        REQUIRED / pending
```

## Native auto-compact trigger: PASS

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

This proves the Codex 0.153.4 threshold trigger, TokenCount persistence/resume restoration and local fallback path under UWA.

## Remote capability shim: implementation/CI PASS

Exact Codex 0.153.4 capability audit selected a narrow compatibility identity: only `[model_providers.uwa].name` becomes `Azure`, while provider id, loopback URL, Responses wire API, disabled OpenAI auth and unrelated config remain unchanged.

Tracked helper/test:

- `tools/codex_remote_compaction_compat.py`
- `tests/test_codex_remote_compaction_compat.py`

Security hardening #351 / run `34164070091` passed.

## Remote V2 ordinary Responses protocol: implementation/CI PASS

Exact 0.153.4 routing:

```text
legacy remote compaction
→ compact_conversation_history()
→ unary /responses/compact

remote compaction V2
→ append compaction_trigger
→ ModelClientSession.stream()
→ ordinary Responses transport
→ /v1/responses for UWA
```

For UWA, `wire_api=responses` and `supports_websockets=false`, so remote V2 uses ordinary HTTP Responses streaming. The V2 collector requires exactly one output item:

```text
type = compaction
encrypted_content = <opaque payload>
```

Tracked implementation now:

- validates exactly one trailing request-only `compaction_trigger`;
- strips it before ChatGPT Web summarization;
- disables tools during bounded compaction summarization;
- encodes the summary into a versioned/bounded/integrity-checked UWA opaque envelope;
- emits exactly one Responses `type=compaction` output plus completed/non-zero usage;
- decodes only valid UWA envelopes back into model-visible compact context on later replayed HTTP history;
- fails closed on foreign/corrupt/oversized envelopes;
- logs only bounded metadata, never summary/envelope bodies.

Exact HTTP `ResponsesApiRequest` has no `previous_response_id`, so `compaction_response_id` is Codex-side checkpoint metadata. Post-compact recovery is carried by replayed compacted history, which the UWA envelope decoder handles directly.

Tracked files:

- `app/services/codex_remote_compaction_v2.py`
- `tests/test_codex_remote_compaction_v2.py`
- `tools/codex_remote_compaction_trigger_probe.py`
- `tests/test_codex_remote_compaction_trigger_probe.py`
- `docs/CODEX_P1_REMOTE_V2_PROTOCOL_GAP_2026-09-08.md`

CI history:

```text
#372  compile/public safety PASS; CI dependency-layer placement failure
#378  492 passed; one probe-test import-identity failure
#380  all jobs PASS, including upstream reproducible regression
```

Security hardening #380 / run `34185500715` is the implementation CI gate.

## Current gate: native remote compaction macOS live

The protocol implementation is no longer blocked on code/CI. The next single gate is real Codex 0.153.4 on macOS with the fail-closed Azure-name compatibility helper enabled for a fresh CLI process.

Required evidence:

```text
THRESHOLD_CROSSED=YES
PRE_TRIGGER_OVER_HARD_CAP=NO
ROLLOUT_COMPACT_MARKER_DELTA>=1
REMOTE_COMPACT_ROUTE_DELTA>=1
REMOTE_COMPACT_SUCCESS_DELTA>=1
AUTO_COMPACT_MODE=REMOTE
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

After this passes, P1.2 still requires a separate same-thread post-remote-compaction recovery of the conversation-only synthetic token through a real local write/read.

## Current status

```text
P1.1 legacy compact endpoint/direct live             PASS
P1.2 native threshold/local fallback                 PASS
P1.2 remote capability shim implementation/CI        PASS
P1.2 remote V2 ordinary Responses implementation/CI  PASS
P1.2 native remote compact macOS live                CURRENT
P1.2 same-thread post-remote recovery                 pending
P1.3 lost-affinity/restart + identity fencing         pending
Desktop UI D1-D5                                      pending / mandatory
```

## Production-hardening order

```text
P1.2 native remote compact live → same-thread recovery
P1.3 lost-affinity / restart + identity fencing + uncertain-effect recovery
Desktop UI live acceptance D1-D5
P1.4 real-project long-task pilot
P2-P5 production hardening / final release gate
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
