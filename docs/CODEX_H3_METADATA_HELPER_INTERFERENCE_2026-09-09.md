# H3 Codex Metadata Helper Interference

Date: 2026-09-09

Status: H3 remains CURRENT. Do not classify the latest UWA wire completion as the H3 agent turn.

## Observed evidence

The latest H3 attempt produced one completed UWA Responses trace with no function calls and no output text. Visual inspection of the controlled ChatGPT browser and the captured request payload then showed that this request was a hidden Codex metadata helper.

The helper request:

- asks for a short UI task title;
- asks for a compact search-oriented thread description;
- embeds the real H3 handoff prompt as data under a user-prompt section;
- explicitly instructs the model to generate metadata instead of solving the embedded task;
- carries normal Codex tool schemas and substantial agent context.

The synthetic H3 workspace still contains the previously completed official effect and does not contain the requested UWA continuation effect. Therefore the H3 continuation has not passed.

## Upstream evidence

Recent OpenAI Codex reports and source history show that thread metadata generation changed materially during August 2026:

- openai/codex #40223 remains open and documents Codex Desktop title generation as a separate GPT-5.6 Luna helper request that inherits broad Codex context and tool definitions.
- openai/codex #41130 remains open and documents hidden search-oriented thread-description generation/backfill requests.
- openai/codex #28741 and PR #29942 document provider-aware fallback work for helper-thread model selection. That fix addresses unsupported helper model IDs and does not provide isolation for a dynamic custom provider such as UWA.
- openai/codex #40492 moved TUI automatic title generation toward bounded ephemeral structured requests and explicitly disabled tools and MCP servers for that helper path.

This upstream behavior is sufficient to explain why a new visible Desktop thread can produce a separate model request before or alongside its actual coding-agent turn.

## H3 interpretation

The earlier `First use exec_command` language-detector repair remains useful for a genuine agent turn. It is insufficient as the sole H3 fix because a metadata helper can contain that same H3 sentence inside the prompt it is summarizing.

A metadata helper must not be treated as proof that the H3 coding-agent turn reached UWA. It also must not trigger the strict required-client-tool contract merely because its embedded source prompt contains an imperative `exec_command` request.

The previous trace shape:

```text
status = completed
function calls = none
output text chars = 0
```

is therefore reclassified as metadata-helper interference, not an H3 agent-tool failure.

## Required bridge repair before another H3 acceptance

Add an explicit request class at the Codex Responses boundary, at minimum distinguishing:

```text
agent_turn
metadata_helper
```

Metadata-helper classification should recognize strong title/description helper signatures and structured-output intent before required-tool detection and web-session affinity handling.

For `metadata_helper` requests:

- do not infer required local tools from the embedded source prompt;
- do not bind the helper to the main agent ChatGPT conversation affinity;
- do not count it as the H3 post-marker agent request;
- expose only safe classification/count metadata in route/wire audits;
- prefer a bounded isolated metadata path. A deterministic local structured response is the smallest release-critical option; a fully isolated helper browser lane is an alternative if model-generated metadata quality is required.

For `agent_turn` requests, retain the existing strict required-tool behavior, UWA browser routing, conversation affinity and route checks.

## Regression requirements

Use a redacted fixture matching the observed helper shape and prove:

1. title/description helper is classified as `metadata_helper`;
2. embedded `First use exec_command` does not trigger required-tool enforcement for that helper;
3. helper completion cannot bind or replace the main agent conversation affinity;
4. route audit reports helper traffic separately from agent traffic;
5. a subsequent real H3 agent turn is still classified as `agent_turn` and can emit the actual client `exec_command` call;
6. the official local effect remains exactly once and the UWA continuation effect is added exactly once only by the real agent turn.

## Gate state

```text
H0 PASS / CLOSED
H1 PASS / CLOSED
H2 PASS / CLOSED
H3 CURRENT / BLOCKED ON METADATA-HELPER ISOLATION
H4 marker foundation present
H5 pending
```

Do not rerun H3 by repeatedly creating fresh Desktop threads until metadata-helper isolation and route-audit classification are implemented and reviewed. Fresh threads can themselves create additional helper requests and make the acceptance trace ambiguous.
