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

## Corrected remote V2 route

Exact Codex 0.153.4 inspection established two separate paths:

```text
legacy remote compact
→ unary /responses/compact

remote compact V2
→ prompt input + compaction_trigger
→ ModelClientSession.stream()
→ ordinary Responses transport
→ /v1/responses for UWA
```

The V2 collector accepts only one `ResponseItem::Compaction`. Since UWA currently handles the trigger request as an ordinary model turn and emits normal message/function-call items, capability selection alone would fail.

P1.1 remains a valid legacy endpoint proof but is not the V2 protocol implementation.

Detailed blocker: `docs/CODEX_P1_REMOTE_V2_PROTOCOL_GAP_2026-09-08.md`.

## Current gate

Implement the ordinary Responses V2 compaction path:

```text
/v1/responses + trailing compaction_trigger
→ validate/strip request-only trigger
→ bounded no-tools ChatGPT Web summary
→ versioned bounded integrity-checked UWA opaque envelope
→ SSE output exactly one type=compaction item
→ response.completed with usable usage
```

Later ordinary Responses translation must decode only valid UWA-owned envelopes into model-visible compact context and fail closed on foreign/corrupt/oversized envelopes. Summary/envelope bodies must never be logged.

After repair/regression/CI, enable the capability shim live and rerun the small-step threshold probe. Then prove same-thread post-remote-compaction recovery before P1.2 closure.

## Current status

```text
P1.1 legacy compact endpoint/live                    PASS
P1.2 native trigger/local fallback                   PASS
P1.2 remote capability shim implementation/CI        PASS
P1.2 remote V2 ordinary Responses repair             CURRENT
P1.2 native remote compact live                      BLOCKED on repair
P1.2 same-thread post-remote recovery                pending
P1.3 affinity/restart/uncertain-effect               pending
Desktop UI live gate D1-D5                           pending / mandatory
```

## Recording discipline

Every live result, failure, repair and disruptive checkpoint is committed before the next step. README, canonical current state, this file, stage/failure records and Draft PR stay aligned. Merge to `main` only after all mandatory gates are green.
