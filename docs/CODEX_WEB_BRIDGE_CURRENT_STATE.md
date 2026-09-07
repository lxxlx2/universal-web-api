# Codex Web Bridge current state

Canonical handoff for the `codex-web-bridge-v2` branch.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while routing model inference through UWA to logged-in ChatGPT Web. Codex remains the local executor for filesystem, shell, edits, tests, Git, sandbox and approval.

## Verified live capabilities

- ordinary UWA / ChatGPT Web inference: PASS
- Codex custom provider: PASS
- GPT-5.6 Sol / High target path: PASS
- real Codex `exec_command`: PASS
- Codex native turn cwd inheritance: PASS
- single-file read/edit/test: PASS
- Stage A multi-file read/edit/test: PASS (`ACCEPTANCE_PASS`)
- Responses `function_call -> function_call_output`: PASS
- V2 metadata wire trace: PASS
- V2 strict required-tool repair can produce a real `exec_command`: PASS

## Current live gate

The minimal acceptance request is:

```text
必须使用 exec_command 执行 pwd。
只返回该命令的真实输出，不要解释，不要推测。
```

Latest live evidence reached a real `exec_command` with arguments containing only `cmd`, no root `workdir`, and Codex executed it in:

```text
/Users/jerson/uwa-codex-acceptance
```

The remaining failure was duplicate execution: after the first local tool result, Codex sent a reconstructed Responses continuation and V2 forced the same required tool again. The command therefore ran twice before the user interrupted the turn.

## Latest diagnosis

Two continuation shapes must be supported:

```text
A. previous_response_id continuation
response_id -> ChatGPT /c/...
```

and the live Codex full-history shape:

```text
B. function_call_output continuation
call_id -> response_id -> ChatGPT /c/...
```

The second shape can contain the original user request, earlier `function_call`, and `function_call_output`. Re-reading the original text must not cause required-tool enforcement after a matching tool output already exists.

## Current V2 fix

Runtime hardening now:

- recognizes completed `function_call + function_call_output` pairs and suppresses duplicate required-tool enforcement;
- remembers process-local metadata-only `call_id -> response_id` mappings when UWA emits a function call;
- uses that call id to recover the already-bound ChatGPT conversation when Codex returns tool output without a usable UWA `previous_response_id`;
- trims reconstructed history to the new `function_call_output` delta before sending it to the reused web conversation;
- stores only call ids, response ids and timestamps in this map; no prompt, command text or tool result text is stored;
- retains the existing degraded same-conversation repair path when local Responses hydration fails;
- retains structured terminal failure handling and compact failure envelopes.

Code commits for this gate:

```text
1f26fae Stop repeated required tools after Codex tool output
9d38ec1 Cover call-id affinity and one-shot required tools
```

Documentation was subsequently updated on the same branch.

GitHub Actions Security hardening run #140 for code head `9d38ec16edd90fbc55cf9092b6c720c9630bcec9` passed, including upstream regression. The later documentation/README head also passed Security hardening #142.

## Expected PASS signal

The next live probe must show exactly one real Codex execution:

```text
exec
/bin/zsh -lc pwd in /Users/jerson/uwa-codex-acceptance
/Users/jerson/uwa-codex-acceptance
```

After `function_call_output`, logs should show call-id affinity recovery and a delta-only browser continuation. There must be no second `pwd` and no new ChatGPT conversation for the tool-result continuation.

Expected useful log markers include:

```text
remembered function call ids for same-web-conversation tool-result continuation
required client tool already has a matching function_call_output; suppressing duplicate enforcement
reusing ChatGPT conversation from function_call_output call_id
trimmed reconstructed Responses history to function_call_output delta for web-session reuse
```

## Acceptance order

Do not resume Stage B until the single-execution / single-web-conversation gate passes.

After that:

```text
Stage B failure recovery
Stage C Git diff discipline
Stage D long process + write_stdin
Stage E same-thread context
Stage F Codex + UWA restart
```

## Continuity

Long-term project truth remains Git tracked docs and code. Additional runtime continuity layers are:

- Codex Desktop thread history;
- private UWA Responses SQLite state at `~/.uwa/codex_responses.sqlite3`;
- in-process ChatGPT web conversation affinity;
- in-process call-id metadata affinity.

UWA mode keeps Codex automatic Memories disabled during acceptance to avoid background memory jobs contending for the controlled ChatGPT tab.

## Public repository safety

Never commit browser profiles, cookies, local storage, tokens, private prompts/source, UWA logs, wire traces, SQLite continuation state or Codex memory workspace content.
