# Codex V2 live affinity retry checkpoint — 2026-09-07

## Live evidence

The macOS acceptance probe was:

```text
必须使用 exec_command 执行 pwd。
只返回该命令的真实输出，不要解释，不要推测。
```

Codex reported the correct native turn workdir:

```text
/Users/jerson/uwa-codex-acceptance
```

The first ChatGPT Web round completed without a real function call. V2 correctly rejected that plain-text result and created a web affinity binding.

Local V2 logs then showed:

```text
[CODEX_WEB_AFFINITY] bound response to ChatGPT conversation
[CODEX_RESPONSES_V2] ... tool_names=['none'] ... web_session_reused=False
[CODEX_WEB_AFFINITY] reusing mapped ChatGPT conversation
[CODEX_V2_RUNTIME] browser turn preparation crashed; converted to response.failed
```

The local affinity endpoint reported `binding_count=1`, proving that the retry reached the mapped-conversation reuse path before failing.

The second metadata trace contained:

```text
response.created
response.failed
function_call_names=[]
required_tool=exec_command
required_tool_satisfied=false
strict_attempt=2
```

It also showed a nearly 1 MiB failure SSE envelope because the failure response echoed request-scale tool metadata.

## First diagnosis and repair

The failure boundary was the strict required-tool retry after a healthy ChatGPT conversation had already been restored. The V2 prepare path restored the mapped `/c/...` conversation and then still required local Responses continuation hydration. If that local hydration raised, the repair never reached ChatGPT Web even though the browser conversation already contained the prior context.

Runtime hardening was updated so that:

1. a healthy mapped ChatGPT conversation can continue a strict repair as an incremental delta when local hydration fails;
2. a real `response.failed` remains the terminal result and is not rewritten as a missing-tool failure;
3. failure envelopes strip request-heavy fields before producing terminal SSE.

## Second live rerun

The next live run advanced further and proved the degraded same-conversation repair path works:

```text
[CODEX_V2_RUNTIME] local continuation hydration failed; continuing the strict repair as a delta on the already-bound ChatGPT conversation
[CODEX_RESPONSES_V2] ... tool_names=['exec_command'] ... web_session_reused=True browser_input=delta
```

The wire trace showed a real `exec_command` function call with only `cmd`, no `workdir`, and `required_tool_satisfied=true`. Codex executed `pwd` in the correct workspace.

However, Codex then executed the same `pwd` a second time. Logs showed a second outer cycle that again started with `web_session_reused=False`, then performed another required-tool repair and emitted another `exec_command`.

## Duplicate-tool diagnosis

The live shape indicates that after local execution Codex can send a reconstructed Responses history containing the earlier user request, the emitted `function_call`, and its `function_call_output`, without a usable UWA `previous_response_id` affinity key.

Two V2 assumptions were incomplete:

1. `required_declared_tool()` could rediscover the original text `必须使用 exec_command` inside reconstructed history and force the tool again even though a matching `function_call_output` already proved that requirement was satisfied.
2. web affinity relied only on `previous_response_id`, so a full-history tool-result continuation could miss the existing ChatGPT `/c/...` binding and create another web conversation.

## Second repair

Runtime hardening now adds a process-local, metadata-only call bridge:

```text
function_call call_id
→ remember call_id -> UWA response_id
→ response_id already maps to ChatGPT /c/...

later function_call_output call_id
→ recover response_id from call_id
→ recover the same ChatGPT /c/...
→ send only function_call_output delta
```

It also detects completed function calls inside reconstructed input. When the original explicit required-tool request already has a matching `function_call` plus `function_call_output`, duplicate required-tool enforcement is suppressed.

When the same conversation is recovered from `call_id`, reconstructed user/function-call history is removed from the browser turn and only the new tool-result item is sent. This prevents both context replay and duplicate command execution.

Only call ids, response ids and timestamps are kept in process memory. Prompt text, command text and tool output are not stored in this map.

## Validation

Regression coverage now includes:

- compact terminal failure envelopes with a 600k-character tool description;
- degraded same-conversation retry state;
- complete function-call detection from reconstructed Responses history;
- extracting `function_call_output` call ids;
- trimming reconstructed input to a tool-result-only delta;
- process-local `call_id -> response_id` recovery;
- recovery of response id and function call ids from minimal Responses SSE.

GitHub Actions Security hardening run #140 for head `9d38ec16edd90fbc55cf9092b6c720c9630bcec9` completed successfully, including the upstream regression suite.

Next live gate remains the single `exec_command(pwd)` probe. Success requires exactly one real Codex `exec`, correct workdir, no repeated `pwd`, and no extra ChatGPT conversation for the tool-result continuation.
