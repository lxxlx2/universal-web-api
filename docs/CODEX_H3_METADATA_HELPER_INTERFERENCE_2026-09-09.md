# Codex H3 Metadata Helper Interference — 2026-09-09

## Status

CURRENT / still release-relevant.

The first H3 UWA-side acceptance attempt produced a completed UWA Responses trace but no local continuation effect. Inspection of the controlled ChatGPT Web request showed that the visible request was a hidden Codex thread-title / search-description metadata helper, not the real coding-agent turn.

The helper request embedded the H3 user task as data for title/description generation and explicitly asked for metadata. Therefore a completed helper response with no client function call does not prove the real H3 agent turn failed to use tools.

## Required architecture

H3 and route audit must distinguish at least:

```text
agent_turn
metadata_helper
```

Classification must happen before required-tool detection, main web-session affinity and authoritative agent-route accounting.

For the first release, metadata helpers should be handled locally with a deterministic bounded structured response when their shape is recognized. They should not consume the main ChatGPT Web coding lane, should not inherit agent-tool requirements, and should not replace the latest authoritative agent-turn route record.

The detector should use structural evidence first and only narrow textual fallback where necessary. Regression coverage must include a sanitized fixture matching the observed title/description helper shape without storing the private H3 prompt.

## Interaction with the browser-send repair

A later H3 diagnostic found an independent ChatGPT browser-send blocker: the idle composer was falsely classified as an old active generation. Commit `1dac853` repaired that issue and a direct High live rerun reached `response.completed` with clean request/browser cleanup.

A tiny Codex CLI probe after that repair also reached `turn.completed`, but the controlled web turn reported that `exec_command` was unavailable. That current client-tool exposure / required-tool diagnosis is separate from metadata-helper classification. Both must be resolved before H3 can close.

## H3 remains open

The official source effect remains the accepted source half. Do not rerun that half merely to investigate UWA behavior.

The next real H3 UWA acceptance must prove all of the following from the actual agent turn:

```text
metadata helper traffic isolated from agent traffic
real client tool call occurs when required
one UWA continuation effect only
official source effect still exactly once
route = uwa / chatgpt / high
```

## Safety

No private prompt body, account identifier, thread identifier, browser identifier, process identifier, cookie, credential, local workspace path, raw trace or tool body is stored in this record.
