# Codex Desktop Web Bridge Progress

This document records the `security-hardening` fork's Codex Desktop integration work so progress is not lost between test sessions.

Checkpoint: **2026-09-06**

## Upstream acknowledgement

This fork is based on [`lumingya/universal-web-api`](https://github.com/lumingya/universal-web-api). Thanks to the original author and contributors for the browser automation, site adapters, streaming parsers, routing, dashboard, and OpenAI/Anthropic compatibility layers that make this experiment possible.

The changes in this fork focus on a narrower idea: keep the upstream browser bridge, harden the default local security boundary, and make Codex Desktop able to use a web chat model as the reasoning backend while Codex itself remains responsible for controlled local tool execution.

## Target architecture

```text
Codex Desktop
    -> OpenAI Responses-compatible request
    -> Universal Web API on 127.0.0.1
    -> controlled browser tab
    -> web chat model decides whether a local client tool is needed
    -> UWA converts the web-model tool request into Responses function_call
    -> Codex executes the tool under its own permission/sandbox policy
    -> function_call_output returns through UWA to the web model
    -> repeat until the task is complete
```

The web page does not receive direct filesystem access. Local file reads, writes, shell commands, and tests must remain client-side Codex operations.

## Verified so far

- hardened localhost launcher and safe default configuration
- browser takeover and persistent isolated browser profile
- `/health`, `/v1/models`, and provider status
- OpenAI Chat Completions compatibility
- OpenAI Responses non-streaming compatibility
- Responses SSE event flow through `response.completed`
- Codex 0.153+ model catalog compatibility via `client_version`
- Codex CLI inference through the custom provider
- Codex Desktop loading the custom `uwa` provider
- official/UWA configuration can be kept separate locally
- Codex catalog now labels the `chatgpt` route as a browser-selected web model instead of pretending it identifies a concrete model
- unmapped `low/high/ultra` reasoning choices are no longer advertised by this fork

## Phase 2 changes implemented in this checkpoint

### Client workspace refusal repair

Real Desktop testing exposed this failure:

> The web model was asked to inspect and fix a local `calc.py`, but answered that it could not access the local machine and returned shell commands for the user to run manually. No `exec_command` function call reached Codex.

UWA tool calling is a text protocol adapter. It describes client tools to the web model and parses XML/JSON tool-call output. A normal web chat model can still fall back to its usual "I cannot access your local files" behavior.

The fork now includes `app/services/client_tool_policy.py` and integrates it into both synchronous and asynchronous tool-call round trips.

Behavior:

1. Only activates when a declared client workspace tool such as `exec_command` is available.
2. Only activates for an apparent local workspace/code request.
3. Only activates before any genuine tool call/result has occurred.
4. Detects a narrow set of English/Chinese local-access refusal patterns.
5. Sends a compact focused repair explaining that the browser has no direct filesystem access while the declared client tool executes locally under Codex sandbox/approval controls.
6. Requires a real tool call instead of asking the user to upload files or run commands manually.
7. Uses bounded retries.
8. Fails closed after repeated false refusals instead of returning an unexecuted manual command as a successful task result.

Tests cover the observed refusal, a successful refusal-to-`exec_command` repair, retry exhaustion, and the important case where a real tool result has already confirmed a missing file. In the latter case the policy does not override the genuine failure.

### Model metadata honesty

The `chatgpt` id means "route to the controlled ChatGPT browser tab". It does not prove which selectable ChatGPT web model is active. The controlled browser remains the source of truth.

Codex metadata now displays `ChatGPT Web (browser-selected model)` for that route and documents this limitation.

### Reasoning metadata honesty

Codex can send `reasoning.effort`, but the current Responses-to-browser conversion does not map that field to ChatGPT web UI reasoning controls. The fork now advertises only a `medium` / Web default placeholder until a stable browser-side mapping exists.

### Context overhead

The hardened `.env.example` disables optional tool-calling prompt padding by default. Focused repair prompts remain available when a tool call needs correction. Existing local `.env` files are not automatically rewritten, so a previously copied config may need manual adjustment.

### Public repository safety

- added [`SECURITY.md`](../SECURITY.md)
- expanded `.gitignore` for future Responses state databases and local `.uwa` runtime state
- progress docs and tests use synthetic examples only
- no real Cookie, token, browser profile, local username, private filesystem path, or private project content should be committed

## Known gaps

### 1. Real Codex Desktop coding-agent acceptance test still pending

The repair logic now has automated unit coverage. It still needs a real browser acceptance test:

```text
clean local workspace
-> read calc.py with client tool
-> modify the deliberately wrong function
-> run a real test
-> receive function_call_output
-> continue the model/tool loop
-> report the verified result
```

A pass here is required before treating the UWA path as ready for normal coding work.

### 2. Responses continuation state is process-local

Current Responses continuation state is in memory, has a one-hour TTL, and disappears when UWA restarts. Long-running Codex threads can therefore lose `previous_response_id` continuity.

Planned direction: optional local persistence with a private runtime database, explicit retention limits, restrictive file permissions, and Git ignore rules. Persistence can contain source code, tool output, and conversation history, so this change needs a dedicated privacy/security review before implementation.

### 3. Token accounting is approximate/missing

Web responses currently report zero token usage. Codex context indicators and compaction decisions should not be assumed to match the real web model context usage.

Planned direction: local approximate token accounting and conservative context metadata after empirical 32K/64K/96K/128K stability tests.

### 4. ChatGPT Memory isolation is not guaranteed

A normal signed-in ChatGPT browser conversation may use account personalization and may create normal chat history. For coding-agent use, account memory and coding context should ideally be isolated.

Planned direction: investigate a stable Temporary Chat workflow. This must be implemented only after current ChatGPT DOM behavior is inspected and tested because UI selectors can change. Until then, users should assume normal account behavior may apply.

### 5. Advanced Codex tools are not guaranteed

Core function tools such as `exec_command` are the first compatibility target. Namespace tools, MCP, plugins, hosted search, multi-agent features, and other Codex-specific capabilities may need separate adapters and tests.

## Security requirements for this public fork

- never commit `.env`, tokens, API keys, cookies, browser profile data, chat transcripts, local logs, request history, or local runtime databases
- keep API and DevTools bindings on loopback by default
- never expose the DevTools port to LAN or the public internet
- keep unsafe Python command execution disabled
- keep automatic upstream self-update disabled in the hardened workflow
- use an isolated browser profile, not a daily personal browser profile
- local Codex tool execution must remain subject to Codex sandbox/approval controls
- do not weaken local permission checks merely to make tool calling easier
- redact screenshots and logs before posting them to this public repository
- if a secret is ever committed, rotate/revoke it immediately and remove it from history when practical

## Current milestone

Phase 1, local security hardening: complete for the tested macOS workflow.

Phase 2, Codex Desktop core agent loop: code-side refusal repair implemented and awaiting real Desktop acceptance testing.

Phase 3, continuity and memory isolation: pending dedicated design and security review.

Phase 4, context accounting and advanced tool compatibility: pending.
