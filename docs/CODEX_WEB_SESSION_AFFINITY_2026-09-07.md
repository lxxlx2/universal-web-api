# Codex Web Session Affinity checkpoint

Date: 2026-09-07
Branch: `codex-web-bridge-v2`

## Live evidence that triggered this change

The V2 short `pwd` probe reached a real Codex client tool and inherited the correct workspace cwd:

```text
workdir: /Users/jerson/uwa-codex-acceptance
provider: uwa
exec
/bin/zsh -lc pwd in /Users/jerson/uwa-codex-acceptance
succeeded
/Users/jerson/uwa-codex-acceptance
```

During the same Codex task, the controlled ChatGPT sidebar accumulated multiple new conversations such as `Require Tool Call`, `Repair Tool Call` and tool-format prompts. The terminal then showed repeated successful executions of the same `pwd` command.

This changed the active diagnosis: local execution and cwd inheritance were working; web-conversation lifecycle was the blocker.

## Root cause

Two independent fresh-chat mechanisms were active:

1. `prepare_and_verify_codex_web_mode()` called `prepare_chatgpt_fresh_composer()` before every outer Codex `/v1/responses` turn. If ChatGPT was already at `/c/...`, the helper clicked `new chat`.
2. The generic ChatGPT site workflow contains a `new_chat_btn` step. Generic UWA conversation reuse is disabled by default because `CONVERSATION_TIMEOUT_THRESHOLD=0`, so a new browser workflow normally runs that step again.

At the same time, Responses continuation reconstructed full history through `previous_response_id`. Therefore every tool result could open a fresh web conversation and replay the transcript. The explicit original instruction to call `exec_command` then remained prominent enough for the web model to request the same command again.

## V2 design

V2 now owns Codex web-conversation creation instead of relying on generic UWA chat lifecycle.

### Response-to-web binding

After a successful browser round:

```text
UWA response_id
→ current validated ChatGPT /c/... pathname
→ target web model
→ reasoning effort
→ in-memory timestamp
```

The map is process-local and bounded by TTL/LRU-style capacity. No conversation content is stored.

Defaults:

```text
UWA_CODEX_WEB_SESSION_AFFINITY=true
UWA_CODEX_WEB_SESSION_TTL_SEC=7200
UWA_CODEX_WEB_SESSION_MAX_ENTRIES=512
```

### Continuation

When Codex sends `previous_response_id`:

1. resolve a matching web binding;
2. restore the mapped ChatGPT conversation if necessary;
3. verify the intended web reasoning/model state;
4. suppress generic workflow `new_chat` behavior for the duration of the Codex browser round;
5. send only the new Responses delta, normally the `function_call_output`;
6. keep full reconstructed history only for Responses state/persistence and safety checks;
7. bind the new UWA response id to the same ChatGPT conversation.

### Fallback

Affinity is deliberately not persistent. If UWA restarts, the mapping expires, the page is unhealthy, or requested model/reasoning changes, V2 falls back to:

```text
fresh ChatGPT conversation
+
reconstructed Responses history
```

This avoids mixing an agent turn into an unrelated browser conversation.

### Internal repair

The generic UWA workflow normally starts new conversations when its reuse threshold is disabled. V2 installs a narrow Codex-only policy overlay on `TabSession.should_start_new_conversation`. It returns `False` only while the selected ChatGPT tab/session carries a request-scoped Codex reuse hint. The hint is enabled around the Codex browser round and cleared in `finally`.

Ordinary UWA requests and non-ChatGPT sites retain their previous lifecycle behavior.

Required-tool retries are also changed from fresh full-history retries to incremental Responses turns chained through the previous attempt response id. This lets a repair remain in the same ChatGPT conversation.

## Privacy and safety

- only validated `/c/...` pathnames are kept in process memory;
- raw paths are not emitted by the status endpoint or normal logs;
- no cookies, local storage, account identifiers, prompt text, command body, source code or tool output are stored in the affinity map;
- no web affinity data is committed;
- the existing private Responses SQLite remains separate;
- Codex sandbox and approval remain authoritative for local execution.

Local status endpoint:

```text
GET /v1/codex/web-affinity
```

It reports only enablement, binding count, TTL/capacity, persistence=false and fallback mode.

## Acceptance gate

Before Stage B resumes, run the minimal `exec_command(pwd)` task again and require all of the following:

```text
real exec_command executes once
cwd = /Users/jerson/uwa-codex-acceptance
no repeated pwd tool loop
one ChatGPT conversation for the tool loop
web-affinity binding_count >= 1 during/after the run
wire trace shows a real exec_command function_call
continuation response reaches a final answer without creating another ChatGPT chat
```

If this gate passes, record it in README/current-state/PR and continue Stage B. If it fails, inspect wire metadata plus the web-affinity status before changing tool prompts again.
