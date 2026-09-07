# Codex Web Bridge Progress

## Branches

- stable verified base: `security-hardening`
- active V2 development: `codex-web-bridge-v2`
- V2 Draft PR: #2

## Verified milestones

```text
Stage A-F protocol/CLI acceptance                    PASS
aggregate A-F checker                                PASS
P1.1 legacy Responses compact direct live            PASS
versioned lifecycle/provider switch CI/live          PASS
P1.2 stream/usage + TokenCount                       PASS
P1.2 native auto-compact trigger/local fallback live PASS
P1.2 remote capability shim implementation/CI #351   PASS
aligned CI/public-safety #355                        PASS
```

## Native trigger live evidence

```text
57429 < 57600
58290 > 57600
ROLLOUT_COMPACT_MARKER_DELTA=1
REMOTE_COMPACT_ROUTE_DELTA=0
REMOTE_COMPACT_SUCCESS_DELTA=0
AUTO_COMPACT_MODE=LOCAL_FALLBACK
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

## Remote capability

Codex 0.153.4 recognizes configured OpenAI/Azure providers for remote compaction V2. `OpenAI` is too broad. A fail-closed helper changes only the managed UWA provider display name to `Azure`, preserving provider id, loopback endpoint, Responses wire API and disabled OpenAI auth.

Tracked files:

- `tools/codex_remote_compaction_compat.py`
- `tests/test_codex_remote_compaction_compat.py`
- `docs/CODEX_P1_REMOTE_COMPACTION_CAPABILITY_AUDIT_2026-09-08.md`

## Current remote V2 protocol blocker

Exact Codex 0.153.4 client inspection corrected an initial assumption: `/responses/compact` is unary HTTP. The client calls `CompactClient.compact_input(...)` and obtains `output: Vec<ResponseItem>`.

The current P1.1 UWA endpoint already has the correct unary transport, but returns assistant message item(s). Remote V2 requires exactly one returned `ResponseItem::Compaction` carrying `encrypted_content`. The V2 collector explicitly fails when the Compaction item count is not exactly one.

Therefore the capability shim remains un-applied on the real macOS config until the item/envelope repair is green.

Detailed blocker: `docs/CODEX_P1_REMOTE_V2_PROTOCOL_GAP_2026-09-08.md`.

## Current gate

```text
legacy compact request without compaction_trigger
→ keep existing P1.1 assistant-message output

V2 compact request with compaction_trigger
→ remove trigger before web summarization
→ bounded no-tools summary
→ UWA opaque bounded envelope
→ unary output=[type=compaction]
```

Later normal UWA Codex Responses translation must decode only UWA-owned envelopes back into model-visible compact context and fail closed on foreign/corrupt envelopes. Summary/envelope bodies must never be logged.

After repair/regression/CI, enable the capability shim live and rerun the small-step threshold probe. Then prove same-thread post-remote-compaction recovery before P1.2 closure.

## Current status

```text
P1.1 legacy compact endpoint/live                    PASS
P1.2 native trigger/local fallback                   PASS
P1.2 remote capability shim implementation/CI        PASS
P1.2 remote V2 unary item/envelope repair            CURRENT
P1.2 native remote compact live                      BLOCKED on repair
P1.2 same-thread post-remote recovery                pending
P1.3 affinity/restart/uncertain-effect               pending
Desktop UI live gate D1-D5                           pending / mandatory
```

## Recording discipline

Every live result, failure, repair and disruptive checkpoint is committed before the next step. README, canonical current state, this file, stage/failure records and Draft PR stay aligned. Merge to `main` only after all mandatory gates are green.
