# Codex Web Bridge Progress

## Branches

- stable verified base: `security-hardening`
- active V2 development: `codex-web-bridge-v2`
- V2 Draft PR: #2

## Verified milestones

```text
Stage A-F protocol/CLI acceptance                    PASS
aggregate A-F checker                                PASS
Responses tool/call-id continuity                    PASS
P1.1 legacy Responses compact direct live            PASS
versioned lifecycle/provider switch CI/live          PASS
P1.2 stream/usage compatibility                      PASS
P1.2 TokenCount persistence/resume                   PASS
P1.2 native auto-compact trigger/local fallback live PASS
P1.2 remote capability shim implementation/CI #351   PASS
latest aligned CI/public-safety #355                 PASS
```

## Native trigger live evidence

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

## Remote capability audit

Codex 0.153.4 recognizes configured OpenAI/Azure providers for remote compaction V2. `OpenAI` is too broad. A fail-closed helper was implemented to change only the managed UWA provider display name to `Azure` while preserving the provider id, loopback endpoint, Responses wire API and disabled OpenAI auth.

Tracked files:

- `tools/codex_remote_compaction_compat.py`
- `tests/test_codex_remote_compaction_compat.py`
- `docs/CODEX_P1_REMOTE_COMPACTION_CAPABILITY_AUDIT_2026-09-08.md`

## Newly confirmed remote V2 blocker

Before enabling the shim on macOS, exact Codex 0.153.4 remote V2 output semantics were compared with UWA P1.1.

P1.1 currently returns unary `output` assistant messages. Remote V2 uses a streaming Responses request and requires exactly one `ResponseItem::Compaction` output item with an opaque `encrypted_content` field. Codex explicitly fails the remote attempt when the compaction item count is not exactly one.

Therefore the capability shim is necessary but cannot yet be enabled live against the legacy endpoint.

Detailed blocker: `docs/CODEX_P1_REMOTE_V2_PROTOCOL_GAP_2026-09-08.md`.

## Current gate

Implement a dual-path compact protocol:

```text
legacy unary request
→ preserve current assistant-message P1.1 behavior

streaming request + compaction_trigger
→ web-backed summary
→ UWA-owned opaque bounded envelope
→ SSE response.output_item.done(type=compaction)
→ response.completed
```

Ordinary Codex Responses web translation must decode only UWA-owned envelopes back into model-visible compact context and reject foreign/corrupt envelopes. No summary or envelope body may be logged.

After regression/CI, enable the capability shim live and rerun the small-step probe. Then prove same-thread post-remote-compaction recovery before closing P1.2.

## Current status

```text
P1.1 legacy compact endpoint/live                    PASS
P1.2 native trigger/local fallback                   PASS
P1.2 remote capability shim implementation/CI        PASS
P1.2 remote V2 response/envelope repair              CURRENT
P1.2 native remote compact live                      BLOCKED on repair
P1.2 same-thread post-remote recovery                pending
P1.3 affinity/restart/uncertain-effect               pending
Desktop UI live gate D1-D5                           pending / mandatory
```

## Roadmap

```text
P1.2 V2 repair → CI → native remote compact → same-thread recovery
P1.3 lost-affinity / restart + identity fencing + uncertain-effect recovery
Desktop D1-D5 actual UI acceptance
P1.4 real-project long-task pilot
P2-P5 production hardening / final release gate
```

## Recording discipline

Every live result, failure, repair and disruptive checkpoint is committed before the next step. README, canonical current state, this file, stage/failure records and Draft PR stay aligned. Merge to `main` only after all mandatory gates are green.
