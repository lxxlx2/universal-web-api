# Current Change Log

## Codex Web Bridge V2 — 2026-09-07

### Active branch

`codex-web-bridge-v2`

### Verified base capabilities

- Codex custom provider through UWA
- ChatGPT Web GPT-5.6 Sol / High target path
- real local `exec_command`
- correct Codex turn cwd inheritance
- single-file read/edit/test
- Stage A multi-file read/edit/test (`ACCEPTANCE_PASS`)
- Responses `function_call -> function_call_output`
- private metadata-only Codex wire tracing

### V2 protocol observability

Added private correlated metadata traces under `~/.uwa/debug/codex-wire`. Metadata mode records event ordering, function-call names and safe argument metadata without storing prompt, command, source or tool-output text.

### Strict required-client-tool contract

Explicit requests such as `必须使用 exec_command` require a real Responses `function_call`. Plain-text simulated command results are rejected and receive bounded repair.

### Root workdir boundary

Accidental generated `workdir="/"` is removed for exec-like client tools unless the user explicitly requests filesystem root. Codex then inherits its native turn cwd.

### ChatGPT Web session affinity

V2 binds UWA response ids to validated ChatGPT `/c/...` paths in process memory. Healthy `previous_response_id` continuations restore that web conversation and send only the new Responses delta.

The generic UWA `new_chat` workflow decision receives a request-scoped Codex reuse hint, so internal tool/repair rounds can remain in one ChatGPT conversation.

### Streaming hardening

Wire trace, continuation persistence and affinity bookkeeping are best-effort and cannot truncate the Responses HTTP stream. Browser-attempt failures are converted to complete structured terminal Responses events.

Failure envelopes remove request-heavy prompt/tool fields before emission.

### Degraded same-conversation repair

If local Responses hydration fails after a valid mapped ChatGPT conversation has already been restored, the strict repair can continue as an incremental browser delta on the existing conversation.

### Full-history tool-result continuation

Latest macOS live testing showed that after a real local tool execution Codex can send reconstructed Responses history containing the original user request, the earlier `function_call`, and its `function_call_output`, without a usable UWA `previous_response_id`. That shape caused the same explicit required tool to execute twice.

V2 now:

- detects matching `function_call + function_call_output` and suppresses duplicate required-tool enforcement;
- records a process-local metadata-only `call_id -> response_id` relation when UWA emits a function call;
- recovers the existing ChatGPT conversation from the returned `function_call_output` call id;
- trims reconstructed history to a tool-result-only browser delta;
- stores no prompt, command text or tool-result content in the call-id map.

Relevant code checkpoints:

```text
1f26fae Stop repeated required tools after Codex tool output
9d38ec1 Cover call-id affinity and one-shot required tools
```

### Current live gate

The next synthetic `exec_command(pwd)` acceptance must show exactly one real local execution in `/Users/jerson/uwa-codex-acceptance`, no repeated `pwd`, and no extra ChatGPT conversation after the tool result.

Stage B-F remain blocked until this minimal gate passes.

### CI

The call-id continuation code head passed Security hardening #140 including upstream regression. Subsequent README/current-state/progress documentation heads also passed the same workflow through #144.
