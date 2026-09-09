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

The controlled ChatGPT page was inspected after the timeout. The diagnostic prompt was still present in the composer and had not become a sent user-message bubble. The send control appeared available in the idle composer. The corresponding private local log showed:

```text
[SEND] pre-send probe classified the page as an old generating/stop state
wait-for-idle timeout configured at 120 seconds
no successful send transition occurred
client_disconnected at 360 seconds
request finalized as cancelled
```

This narrows the root cause substantially: the direct High request did not stall after a successful ChatGPT model submission. UWA filled the composer, then its pre-send generation/stop-state detector incorrectly blocked submission on a page that visually appeared idle. The outer Responses layer kept emitting progress heartbeats while the browser workflow waited, so the client observed a live stream without useful model output.

The earlier Medium direct probe is separate evidence: it failed immediately during Web-mode verification because the controlled ChatGPT Web state was High while the probe requested Medium. The High probe passed that preflight and exposed the pre-send state-detection blocker.

## Current interpretation

The primary browser-path blocker is now the pre-send state probe, not response parsing and not Codex CLI transport.

Relevant implementation behavior in `app/core/workflow/executor_send.py` treats any of these signals as a confirmed generating/stop state:

```text
generating
sendLooksLikeStop
stopBtnFound
```

The ChatGPT configuration also uses network mode with a 600-second browser hard timeout, which matches the historical approximately 600-second stuck-session cancellations seen in private local logs. The direct curl client was shorter at 360 seconds and therefore disconnected before that browser-side stuck timeout.

Next repair should be narrowly scoped to ChatGPT send-state detection and must:

- capture which exact signal/selector causes the false positive on the current ChatGPT composer;
- distinguish a visible send button from a genuine stop-generation control;
- avoid treating stale or hidden DOM nodes as active generation;
- fail boundedly if pre-send state is ambiguous instead of holding a request for many minutes;
- preserve the existing safe behavior for a genuinely active generation;
- add focused regression coverage with the current ChatGPT idle-composer shape;
- prove the direct High probe actually submits and reaches `response.completed` before returning to Codex CLI/H3 testing.

Do not treat Codex CLI 0.153.4 as the primary root cause until this browser pre-send blocker is resolved and the direct High probe can complete.

## Safety

No private prompt content, account identifiers, thread identifiers, browser identifiers, process identifiers, cookies, credentials, or raw private traces are stored in this record.
