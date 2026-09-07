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

## Diagnosis

The remaining failure was no longer cwd handling, local `exec_command` execution, or initial web affinity creation. The failure boundary was the strict required-tool retry after a healthy ChatGPT conversation had already been restored.

The V2 prepare path restored the mapped `/c/...` conversation and then still required local Responses continuation hydration. If that local hydration raised, the repair never reached ChatGPT Web even though the browser conversation already contained the prior context.

The strict layer then interpreted the terminal `response.failed` as another missing-tool result, which hid the actual preparation failure behind `required_client_tool_not_called`.

## Repair

Runtime hardening now applies three rules:

1. If a previous response is already bound to a healthy ChatGPT conversation and local continuation hydration fails, continue the strict repair as an incremental delta on that same bound conversation. The retry keeps its input, tools, and tool choice while clearing the local `previous_response_id` hydration handle.
2. If a strict attempt returns a real `response.failed`, preserve that terminal failure. Do not rewrite it as a missing-tool error.
3. Failure envelopes remove request-heavy tool schemas, prompts, metadata, and continuation handles before building terminal SSE frames, preventing multi-hundred-kilobyte diagnostic responses.

This degraded live path is intentionally scoped to an already-verified in-process web binding. When no healthy binding exists, the normal fresh-chat plus reconstructed-history fallback remains authoritative.

## Validation

Added regression coverage for:

- compact terminal failure envelopes even with a 600k-character tool description;
- degraded same-conversation retry state preserving the repair delta and declared tools while clearing `previous_response_id`;
- existing complete `response.created -> response.failed` terminal sequence.

Next live gate remains the same single `exec_command(pwd)` probe. Success requires one real Codex `exec` execution, correct workdir, no repeated `pwd`, and no extra ChatGPT conversation for the strict repair.
