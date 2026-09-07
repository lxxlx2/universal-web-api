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

The following explanations are now rejected by live evidence:

1. stale `models_cache.json` advertising a larger context window;
2. live `/v1/models` advertising a larger context window;
3. explicit top-level context-window / auto-compact overrides;
4. a visible local-summary compaction lifecycle during rounds 1-7.

## Current hypothesis

The acceptance runner uses one fresh `codex exec resume` process per filler turn. A plausible remaining failure mode is that resumed CLI processes reconstruct conversation history but do not restore the prior process's in-memory token-usage state before the next pre-turn auto-compact check.

If so, each resumed process can begin with insufficient token accounting, perform one oversized sampling request, receive the current turn's non-zero usage only after sampling, then exit because the filler reply requires no tool follow-up. The next process would repeat the same pattern. This would explain why input usage can exceed the advertised 64K window without either remote compact or visible local compact.

This hypothesis is not yet accepted as fact. The next step is source-level verification against the exact Codex 0.153.4 release (`rust-v0.153.4`, commit `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`) for resume/history/token-info restoration behavior.

## Gate

Do not rerun the full stress test and do not change provider identity until the resume/token-usage restoration path is verified.
