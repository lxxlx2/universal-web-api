# Codex Direct High Browser Stall — 2026-09-09

## Status

RESOLVED / LIVE PASS on 2026-09-10 for the browser-send blocker on `codex-web-bridge-v2`.

A direct local `curl` request to UWA `/v1/responses` with `model=chatgpt`, `stream=true`, and `reasoning.effort=high` originally bypassed Codex CLI/Desktop and reproduced a 360-second stall. The Responses stream stayed alive with periodic `response.in_progress`, but the controlled ChatGPT page still showed the diagnostic prompt sitting unsent in the composer.

Private local logs showed the real browser workflow was blocked before submission:

```text
[SEND] pre-send probe classified the page as an old generating/stop state
wait-for-idle timeout configured at 120 seconds
no successful send transition occurred
client disconnected after the outer direct probe timeout
```

The root cause was a false positive in generic page-level pre-send generation detection. The current ChatGPT idle composer exposed a ready send button, while unrelated page-level stop/streaming-like signals caused `_wait_for_send_idle_before_action()` to hold the request instead of clicking send.

## Repair

Commit `1dac853` adds a narrow ChatGPT-specific idle-composer readiness check in `app/core/workflow/executor_send.py`.

For `chatgpt.com`, the new gate accepts the composer as ready only when the actual configured send button is:

- present and visible;
- enabled;
- identified as `data-testid="send-button"`;
- free of stop/cancel/abort semantics.

When that exact ready-send state is verified, unrelated page-level stop/streaming indicators are ignored for the pre-send gate. If the helper cannot prove the composer is ready, the existing conservative generation/stop-state guard remains authoritative.

## Live proof

After the repair, the same direct High diagnostic completed successfully through the real browser path:

```text
ChatGPT composer ready check = PASS
prompt actually submitted = YES
assistant output = DIRECT_UWA_HIGH_OK
response.completed = YES
browser returned to idle = YES
request_manager running_count after completion = 0
```

This closes the direct browser-send/SSE stall that previously reproduced independently of Codex CLI.

A tiny post-fix `codex exec` probe also reached `turn.completed` without the earlier five-minute `stream disconnected before response.completed` failure. However, the controlled ChatGPT turn reported that the expected `exec_command` client tool was not available, so the local tool call did not occur. That is a separate client-tool exposure / required-tool-path blocker and is now the next investigation layer.

## Current interpretation

The repaired path is now:

```text
Codex or direct Responses request
→ UWA Web-mode preflight
→ ChatGPT composer fill
→ ChatGPT idle-composer readiness check
→ real send
→ browser/model completion
→ terminal Responses event
```

The remaining H3 work must not reopen this browser-send blocker unless a new live reproduction appears. Current focus is to determine, from metadata-only wire evidence, whether `exec_command` is absent from the client request, present but not exposed to the web turn, or present with required-tool detection missed.

## Safety

No private prompt content, account identifiers, thread identifiers, browser identifiers, process identifiers, cookies, credentials, raw private traces, local workspace paths, or usage quantities are stored in this record.
