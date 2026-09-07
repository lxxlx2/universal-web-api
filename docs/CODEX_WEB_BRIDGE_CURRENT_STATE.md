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

Security hardening #351 / run `34164070091` passed. Aligned docs/public-safety #355 / run `34164304589` also passed.

## Current blocker: remote V2 compaction item/envelope protocol

The real macOS Azure-name shim has NOT been enabled yet because a pre-live exact-release audit found an additional output-item mismatch.

Important corrected transport fact: Codex 0.153.4 `/responses/compact` is still **unary HTTP**. `ModelClientSession` calls `CompactClient.compact_input(...)` and receives `output: Vec<ResponseItem>`; the client later exposes those items internally to the V2 collector.

Current UWA P1.1 unary response contains assistant message items. Remote V2 requires the unary output list to contain exactly one:

```text
type = compaction
encrypted_content = <opaque payload>
```

The V2 collector fails if the Compaction item count is not exactly one. Enabling the capability shim against the current P1.1 item shape would therefore be a predictable failure.

Detailed blocker: `docs/CODEX_P1_REMOTE_V2_PROTOCOL_GAP_2026-09-08.md`.

## Current repair gate

Preserve P1.1 behavior for compact requests without `compaction_trigger`. For V2 trigger requests:

1. remove the request-only trigger before web summarization;
2. generate the bounded no-tools summary;
3. encode it in a UWA-owned bounded opaque envelope with integrity checks;
4. return unary `output` containing exactly one `type=compaction` item;
5. decode only UWA-owned compaction envelopes into model-visible compact context on later normal Codex Responses turns;
6. fail closed on foreign/corrupt envelopes;
7. never log summary or envelope contents.

The upstream field is named `encrypted_content`; UWA does not claim its local envelope is OpenAI encryption.

## Current status

```text
P1.1 legacy compact endpoint/direct live             PASS
P1.2 native threshold/local fallback                 PASS
P1.2 remote capability shim implementation/CI        PASS
P1.2 remote V2 unary item/envelope protocol repair   CURRENT
P1.2 native remote compact macOS live                BLOCKED on repair
P1.2 same-thread post-remote recovery                 pending
P1.3 lost-affinity/restart + identity fencing         pending
Desktop UI D1-D5                                      pending / mandatory
```

## Production-hardening order

```text
P1.2 V2 item/envelope repair → CI → native remote compact live → same-thread recovery
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
