# P1.2 model-cache / resume diagnosis — 2026-09-08

## Scope

Read-only diagnosis after the second full macOS P1.2 large-context run failed without any observed `/v1/responses/compact` activity.

## Live facts

Installed client:

```text
codex-cli 0.153.4
```

Successful filler turns reported monotonically growing input usage:

```text
21230
42219
70125
104948
146688
195345
250919
```

Rounds 1-7 contained only `agent_message` completion events. No compact / summary / context lifecycle item was present. Round 8 emitted `error` + `turn.failed` and no usage object.

## Model catalog/cache

`~/.codex/models_cache.json` existed and matched client version `0.153.4`.

The cached `chatgpt` entry resolved to:

```text
context_window=64000
max_context_window=64000
auto_compact_token_limit=null
effective_context_window_percent=95
truncation_policy=tokens:57600
comp_hash=null
use_responses_lite=false
```

The live UWA `/v1/models?client_version=0.153.4` response also advertised the same 64K context window and 57,600-token truncation policy. There is therefore no evidence that an old or mismatched model cache caused the missing compaction.

## Codex config

The active top-level configuration had:

```text
model='chatgpt'
model_provider='uwa'
model_context_window=None
model_auto_compact_token_limit=None
model_auto_compact_token_limit_scope=None
```

The UWA provider remained a normal custom Responses provider:

```text
name='Universal Web API'
wire_api='responses'
requires_openai_auth=false
supports_websockets=false
```

No top-level context-window or auto-compact override explains the behavior.

## Runtime health

UWA service remained healthy and the controlled browser remained connected during the diagnostic.

## Closed hypotheses

The following explanations are rejected by live evidence:

1. stale `models_cache.json` advertising a larger context window;
2. live `/v1/models` advertising a larger context window;
3. explicit top-level context-window / auto-compact overrides;
4. a visible local-summary compaction lifecycle during rounds 1-7;
5. fresh `codex exec resume` processes inherently discarding persisted token usage.

## Exact Codex 0.153.4 source verification

The installed release `rust-v0.153.4` resolves to upstream commit:

```text
3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

That release already contains explicit token-usage restoration on resume/fork. During `InitialHistory::Resumed`, Codex scans the recorded rollout for the latest `EventMsg::TokenCount` and seeds session state with its `TokenUsageInfo` before the next real turn.

The normal sampling path also records usage from `response.completed`, then emits a `TokenCount` event. `send_event_raw` persists ordinary events as `RolloutItem::EventMsg`, so the intended 0.153.4 design is for non-zero response usage to survive a later CLI resume.

Therefore process restart alone does not explain the missing pre-turn compaction.

## Real rollout TokenCount result

A bounded read-only inspection of the actual private P1.2 rollout found exactly one matching rollout and nine persisted `TokenCount` events. No thread ID, rollout pathname, prompts, response bodies, tool payloads, or other private content was published.

Safe numeric evidence:

```text
TOKENCOUNT_EVENTS=9
TOKENCOUNT_PERSISTED=YES
TOKENCOUNT_MODEL_WINDOWS=60800
```

The persisted records progressed as follows:

```text
ordinal  total_tokens  last_tokens
1             7213        7213
2            21343       14130
3            42390       21047
4            70354       27964
5           105235       34881
6           147033       41798
7           195748       48715
8           251380       55632
9           251380       55632
```

Important interpretation boundary: the diagnostic script compared `last_tokens` with `57,600`, but this comparison is not yet accepted as Codex's actual pre-turn compaction rule. The rollout simultaneously contains cumulative `total_tokens` far above the configured window and per-response `last_tokens` below 57,600. The next source-level gate is therefore the exact `context_window_token_status()` implementation in Codex 0.153.4: determine which token quantity and which effective window/auto-compact limit it uses.

The observed `model_context_window=60800` is consistent with the cached 64,000 context window after Codex's 95% effective-context-window factor. This is evidence that the model metadata is being applied, not that the threshold decision itself is correct.

The rollout inspection reported zero `turn_started` lifecycle events under the event names used by the diagnostic. This does not prove that later turns were absent: the acceptance itself demonstrably ran multiple resumed turns, and the event naming/layout may differ. Consequently `OVER_THRESHOLD_TOKENCOUNT_BEFORE_LATER_TURN=NO` is not treated as proof that no over-threshold token state preceded a later resume.

## Current fault boundary

The usage persistence chain is now confirmed working:

```text
UWA response usage
→ Codex TokenUsageInfo
→ TokenCount event
→ rollout persistence
→ resume-capable state
```

The current question is narrower:

```text
persisted token state
→ context_window_token_status()
→ token_limit_reached ?
→ run_auto_compact()
```

Do not change provider identity or rerun the full stress test until the exact 0.153.4 token-limit calculation is verified.

## Gate

Inspect the exact `rust-v0.153.4` implementation of `context_window_token_status()` and its helpers. Only after that source fact is established should the project decide whether the remaining blocker is token accounting semantics, local fallback behavior, or a narrow remote-compaction capability shim.
