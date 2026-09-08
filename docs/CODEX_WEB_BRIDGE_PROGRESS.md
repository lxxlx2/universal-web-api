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
P1.2 remote V2 implementation/CI #380                PASS
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

## Remote V2 implementation

Exact Codex 0.153.4 route:

```text
remote compact V2
→ prompt history + trailing compaction_trigger
→ ModelClientSession.stream()
→ ordinary Responses HTTP
→ /v1/responses
```

The implementation in `app/services/codex_remote_compaction_v2.py` now:

```text
valid trailing trigger
→ strip trigger
→ no-tools bounded ChatGPT Web compact summary
→ UWA versioned/bounded/integrity-checked opaque envelope
→ exactly one type=compaction output item
→ response.completed with non-zero usage
```

On future client-replayed compacted history, only valid UWA envelopes are decoded into model-visible compact context. Foreign/corrupt/oversized envelopes fail closed.

Exact 0.153.4 HTTP Responses requests do not use `previous_response_id`, so post-compact summary recovery is based on client-replayed compacted history rather than a compact-response server handle.

Live evidence now uses `tools/codex_remote_compaction_trigger_probe.py`, which counts V2-specific metadata markers rather than the legacy `/responses/compact` route.

CI history:

```text
#372 compile/public-safety PASS; lightweight CI dependency placement defect
#378 492 tests PASS; one wrapper test module-identity defect
#380 all jobs PASS
```

Run #380: `34185500715`.

## Current gate: native remote compact macOS live

Required output:

```text
THRESHOLD_CROSSED=YES
PRE_TRIGGER_OVER_HARD_CAP=NO
ROLLOUT_COMPACT_MARKER_DELTA>=1
REMOTE_COMPACT_ROUTE_DELTA>=1
REMOTE_COMPACT_SUCCESS_DELTA>=1
AUTO_COMPACT_MODE=REMOTE
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

After that, run a separate same-thread recovery gate that recovers the first-turn conversation-only synthetic token through a real local write/read without searching local session/history stores.

## Current status

```text
P1.1 legacy compact endpoint/live                    PASS
P1.2 native trigger/local fallback                   PASS
P1.2 remote capability shim implementation/CI        PASS
P1.2 remote V2 implementation/CI                     PASS
P1.2 native remote compact live                      CURRENT
P1.2 same-thread post-remote recovery                pending
P1.3 affinity/restart/uncertain-effect               pending
Desktop UI live gate D1-D5                           pending / mandatory
```

## Recording discipline

Every live result, failure, repair and disruptive checkpoint is committed before the next step. README, canonical current state, this file, stage/failure records and Draft PR stay aligned. Merge to `main` only after all mandatory gates are green.
