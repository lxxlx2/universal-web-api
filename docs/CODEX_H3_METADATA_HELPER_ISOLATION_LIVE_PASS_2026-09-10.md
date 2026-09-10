# Codex H3 metadata-helper isolation — LIVE PASS — 2026-09-10

## Result

The H3 metadata-helper isolation blocker is PASS / LIVE / CLOSED.

A current-Codex hidden thread-title style request was routed through the new local metadata-helper path. The request carried an embedded client-tool instruction as untrusted prompt data, but classification occurred before required-tool detection, ChatGPT Web preparation, web-session affinity and authoritative agent-route accounting.

## Live evidence

```text
metadata helper classification = YES
response.completed = YES
function call emitted = NO
bounded structured title returned = YES
UWA running request count after helper = 0
new metadata-only trace kind = metadata_helper
route-audit agent request count after helper = 0
route-audit agent response count after helper = 0
```

The helper therefore did not consume the ChatGPT Web coding lane, did not invoke the embedded `exec_command` instruction, did not leave an orphan request and did not replace agent-turn route evidence.

## Implementation

Commit `de875e4` adds the release-scoped isolation path:

```text
request classification before agent-tool logic
metadata_helper vs agent_turn metadata in wire summaries
local deterministic structured metadata response
metadata-helper exclusion from route-audit agent traffic
```

The current upstream Codex title generator uses a hidden temporary structured thread and a bounded title schema. UWA mirrors only the narrow observed metadata shape needed for release safety and does not attempt to generalize arbitrary hidden Codex traffic.

## H3 status after this pass

The earlier browser-send blocker is closed, and the required real-client-tool path is also live-proven: `exec_command` was detected, emitted, executed by Codex, returned as `function_call_output`, followed by `response.completed`, with zero running requests afterward.

The remaining H3 work is the final synthetic official-to-UWA handoff acceptance in the preserved workspace. It must prove exactly one official source effect, exactly one UWA continuation effect, a real UWA agent tool turn, and authoritative `uwa / chatgpt / high` route evidence.

## Safety

No private prompt body, account identifier, raw thread identifier, browser identifier, process identifier, cookie, credential, local workspace path, raw wire trace or tool output is recorded here.
