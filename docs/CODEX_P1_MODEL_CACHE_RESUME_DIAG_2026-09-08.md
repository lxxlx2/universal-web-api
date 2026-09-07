# P1.2 model-cache / resume diagnosis — 2026-09-08

## Scope

Read-only diagnosis after the second full macOS P1.2 large-context run failed without any observed `/v1/responses/compact` activity.

## Live facts

Installed client:

```text
codex-cli 0.153.4
```

Successful filler turns reported monotonically growing CLI usage:

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

The following explanations are rejected by live evidence/source inspection:

1. stale `models_cache.json` advertising a larger context window;
2. live `/v1/models` advertising a larger context window;
3. explicit top-level context-window / auto-compact overrides;
4. a visible local-summary compaction lifecycle during rounds 1-7;
5. fresh `codex exec resume` processes inherently discarding persisted token usage;
6. UWA fallback usage being accidentally double-subtracted by `TokenUsageInfo`.

## Exact Codex 0.153.4 source verification

The installed release `rust-v0.153.4` resolves to upstream commit:

```text
3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

That release already contains explicit token-usage restoration on resume/fork. During `InitialHistory::Resumed`, Codex scans the recorded rollout for the latest `EventMsg::TokenCount` and seeds session state with its `TokenUsageInfo` before the next real turn.

The normal sampling path records usage from `response.completed`, then emits a `TokenCount` event. `send_event_raw` persists ordinary events as `RolloutItem::EventMsg`, so the intended 0.153.4 design is for non-zero response usage to survive a later CLI resume.

`TokenUsageInfo::append_last_usage()` adds each response's usage to `total_token_usage` while preserving that response unchanged as `last_token_usage`. Therefore the CLI's cumulative token numbers and rollout's per-response `last_tokens` serve different purposes and are both expected.

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

The `model_context_window=60800` value is exactly the cached 64,000 window after Codex's 95% effective-context-window factor.

## Exact token-limit semantics

Codex 0.153.4 `context_window_token_status()` calls `sess.get_total_token_usage()`. Despite its name, the exact implementation of the underlying history method uses:

```text
last_token_usage.total_tokens
+ tokens added after the last model-generated item
+ optional reasoning-history estimate
```

It does not use the monotonically accumulated `total_token_usage.total_tokens` as the active context size.

The hard full-context limit is:

```text
resolved_context_window * effective_context_window_percent / 100
= 64000 * 95 / 100
= 60800
```

Therefore the last successful filler turn ended with active context around `55,632`, still below the 60,800 hard limit. The absence of auto-compaction before round 8 is expected from the exact token-limit calculation.

## Exact pre-turn ordering

The decisive source fact is in Codex 0.153.4 `run_turn()` itself. Pre-turn compaction executes before context updates and before the new user message are recorded. The source contains an explicit TODO stating that pending incoming items are not yet estimated for this pre-turn decision.

Consequently round 8 began with only the prior successful active-context estimate (`55,632 < 60,800`). Codex correctly skipped pre-turn compaction. The acceptance runner then added another ~20KB filler only after that check, allowing the next sampling request to jump across the effective context boundary in one step. Round 8 then failed the filler contract before it could produce a new successful `TokenCount` above the threshold.

This means the second full P1.2 failure is primarily an acceptance-runner threshold-crossing defect, not evidence that Codex's pre-turn auto-compaction trigger failed.

## Remote compaction capability remains separate

A separate exact-release fact still stands: the normal UWA custom provider is classified `RemoteCompactionSupport::Unsupported`, while recognized OpenAI/Azure providers can advertise remote compaction. Thus once a future turn genuinely reaches the pre-turn threshold, the current provider identity should select Codex's local fallback path unless a narrowly justified capability solution is added.

Do not conflate this provider-capability issue with the round-8 threshold-crossing defect.

## Current fault boundary

The verified chain is now:

```text
UWA response usage
→ Codex TokenUsageInfo
→ TokenCount event
→ rollout persistence
→ resume restoration
→ active-context calculation from last response usage
→ pre-turn compact check BEFORE new user input
```

The next acceptance must approach the 60,800 boundary without a 20KB jump. It should use smaller filler near the limit, complete one turn with a successful `last_token_usage` above threshold, and then send a very small next-turn trigger so pre-turn auto-compaction is observable before ordinary sampling.

## Gate

Repair the P1.2 live runner's threshold-approach strategy and add regression coverage for adaptive/small filler near the effective window. Do not change provider identity yet. First prove the exact auto-compact trigger path under the current provider; then distinguish local fallback behavior from the separate remote `/v1/responses/compact` capability gate.
