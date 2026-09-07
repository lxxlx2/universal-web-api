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
4. a visible local-summary compaction lifecycle during rounds 1-7.

A fifth hypothesis was investigated and rejected by exact-release source inspection: fresh `codex exec resume` processes do not inherently discard persisted token usage.

## Exact Codex 0.153.4 source verification

The installed release `rust-v0.153.4` resolves to upstream commit:

```text
3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

That release already contains explicit token-usage restoration on resume/fork. During `InitialHistory::Resumed`, Codex scans the recorded rollout for the latest `EventMsg::TokenCount` and seeds session state with its `TokenUsageInfo` before the next real turn.

The normal sampling path also records usage from `response.completed`, then emits a `TokenCount` event. `send_event_raw` persists ordinary events as `RolloutItem::EventMsg`, so the intended 0.153.4 design is for non-zero response usage to survive a later CLI resume.

Therefore process restart alone does not explain the missing pre-turn compaction.

## Remaining diagnostic question

The next fact to establish is whether this actual P1.2 thread's private rollout contains the expected persisted `TokenCount` events and, if so, what safe numeric token totals they contain near rounds 2-4.

Two outcomes are possible:

1. `TokenCount` is absent or carries zero/incorrect totals: the bridge/client usage persistence chain remains the blocker;
2. `TokenCount` contains the expected over-threshold usage before a later resumed turn: pre-turn token-limit/compaction selection becomes the next fault boundary.

Do not print prompts, response bodies, thread IDs, response IDs, tool payloads, credentials, or the full rollout. Only bounded event-type counts and numeric token fields are acceptable public evidence.

## Gate

Do not rerun the full stress test and do not change provider identity until the real rollout `TokenCount` persistence/restoration fact is known.
