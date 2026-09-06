# Codex Desktop Web Bridge Progress

This document records the security-hardening fork's Codex Desktop integration work so progress is not lost between test sessions.

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

## Known gaps found during real Codex Desktop testing

### 1. Local coding tool loop is not yet reliable

Observed failure: for a request to inspect and fix a local `calc.py`, the web model answered that it could not access the local machine and returned shell instructions to the user. No `exec_command` function call reached Codex.

Cause: UWA currently emulates tool calling by describing client tools to the web model in text and parsing XML/JSON tool-call output. A web chat model can still fall back to its normal "I cannot access your local files" behavior.

Current remediation: add a Codex/client-workspace policy that explicitly explains that client tools execute on the user's machine and automatically retries obvious local-access refusal answers when `exec_command` or equivalent client tools are available.

### 2. Model identity is indirect

The `chatgpt` model id currently means "route to the ChatGPT browser tab". It does not prove which selectable ChatGPT web model is active. The controlled browser remains the source of truth for the actual selected web model.

The Codex catalog should therefore describe this route as a browser-selected ChatGPT model and avoid presenting unsupported reasoning levels as if they were mapped.

### 3. Reasoning level is not mapped yet

Codex can send `reasoning.effort`, but the current Responses-to-browser conversion does not map that field to the ChatGPT web UI's reasoning controls. Advertising `low/medium/high/ultra` is misleading until a stable UI mapping exists.

### 4. Responses continuation state is process-local

Current Responses continuation state is in memory, has a one-hour TTL, and disappears when UWA restarts. Long-running Codex threads can therefore lose `previous_response_id` continuity.

Planned direction: optional local persistence with a private runtime database, explicit retention limits, file permissions, and Git ignore rules. Persistence must remain opt-in or clearly documented because it can contain source code, tool output, and conversation history.

### 5. Token accounting is approximate/missing

Web responses currently report zero token usage. Codex context indicators and compaction decisions should not be assumed to match the real web model context usage.

Planned direction: local approximate token accounting and conservative context metadata after empirical 32K/64K/96K/128K stability tests.

### 6. ChatGPT Memory isolation is not guaranteed

A normal signed-in ChatGPT browser conversation may use account personalization and may create normal chat history. For coding-agent use, account memory and coding context should ideally be isolated.

Planned direction: investigate a stable Temporary Chat workflow. This must be implemented cautiously because UI selectors can change. Until then, users should understand that normal ChatGPT account behavior may apply.

### 7. Advanced Codex tools are not guaranteed

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
- if a secret is ever committed, remove it from history when practical and rotate/revoke it immediately

## Current milestone

Phase 1, local security hardening: complete for the tested macOS workflow.

Phase 2, Codex Desktop core agent loop: in progress. Acceptance test is a clean local workspace where Codex can read `calc.py`, fix a deliberately incorrect function, run a real test, and report the verified result without asking the user to execute commands manually.

Phase 3, continuity and memory isolation: pending.

Phase 4, context accounting and advanced tool compatibility: pending.
