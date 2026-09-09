# Codex Direct High Browser Stall — 2026-09-09

## Status

Release-critical blocker confirmed on `codex-web-bridge-v2`.

A direct local `curl` request to UWA `/v1/responses` with `model=chatgpt`, `stream=true`, and `reasoning.effort=high` bypassed Codex CLI/Desktop and reached the ChatGPT Web execution path.

Observed behavior:

```text
Web-mode preflight accepted High
Responses stream remained connected
periodic response.in_progress events continued
no response.completed
no response.failed
no model output text
direct curl client timed out at 360 seconds
```

This proves that the current long-running failure is not solely a Codex CLI custom-provider regression. The direct UWA -> ChatGPT Web browser execution path itself can remain in progress without a terminal model result.

The earlier Medium direct probe is separate evidence: it failed immediately during Web-mode verification because the controlled ChatGPT Web state was High while the probe requested Medium. The High probe passed that preflight and exposed the deeper browser execution stall.

## Current interpretation

The HTTP/SSE connection itself stays alive. The missing condition is a terminal browser/model result that UWA can translate into `response.completed` or `response.failed`.

The next investigation should focus on the browser workflow/network monitor/request lifecycle beneath `_run_chat_completion_final`, especially:

- whether the ChatGPT Web send action actually creates the intended model request;
- whether the network monitor attaches to the correct request/response stream;
- whether repeated upstream progress events keep the workflow alive without useful content;
- whether the configured hard execution timeout is actually enforced on this browser path;
- whether client disconnect at 360 seconds cancels and releases the underlying browser request promptly.

Do not treat Codex CLI 0.153.4 as the primary root cause until this direct browser-path stall is resolved and the direct High probe can complete.

## Safety

No private prompt content, account identifiers, thread identifiers, browser identifiers, process identifiers, cookies, credentials, or raw private traces are stored in this record.
