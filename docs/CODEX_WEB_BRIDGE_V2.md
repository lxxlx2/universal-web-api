# Codex Web Bridge V2

This document is the implementation-oriented V2 companion. Canonical live status is maintained in:

- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`

## Goal

Keep official Codex Desktop / CLI as the local executor for filesystem, shell, edits, tests, Git, sandbox and approvals while allowing controlled inference through the local UWA bridge to a logged-in ChatGPT Web session.

The bridge translates between Codex Responses semantics and ChatGPT Web conversation turns. Local client tools remain client-side. UWA must not fabricate tool execution or treat browser-only text as proof of a local side effect.

## Current release-critical status

```text
Stage A-F protocol/CLI acceptance                  PASS
P1.1 compact direct live                           PASS
P1.2 stream/usage/remote compaction                PASS
P1.3 continuity/restart/retry safety               PASS / CLOSED
Hybrid H0-H2                                       PASS
Desktop D1-D5                                      PASS / LIVE / CLOSED
ChatGPT idle-composer send repair                  PASS / LIVE
Hybrid H3                                          CURRENT
Hybrid H4-H5                                       pending
```

H3 has an accepted official source half. The UWA half is still open because two independent issues were observed during acceptance:

1. hidden Codex title/description metadata-helper requests can be mistaken for the real agent turn;
2. after the browser-send false positive was fixed, a tiny Codex CLI agent probe completed transport successfully but the controlled web turn reported that `exec_command` was unavailable.

Commit `1dac853` closes the browser-send blocker. A direct High live probe now submits the composer, returns the expected model output, emits `response.completed`, returns the browser tab to idle and leaves no running request. Current diagnosis is therefore the client-tool exposure / required-tool layer plus metadata-helper isolation.

## Core protocol requirements

The bridge must preserve:

```text
Responses request
→ model/reasoning verification
→ ChatGPT Web turn
→ structured function_call when a client tool is required
→ Codex executes locally
→ function_call_output
→ same logical web conversation continuation
→ terminal model answer
```

A plain-text imitation of command output is never accepted as a client tool call.

## Web-session affinity

V2 binds Responses continuity to the ChatGPT Web conversation through response/call metadata only. It does not persist prompt bodies or tool output in the affinity index.

Normal path:

```text
initial Responses turn
→ fresh ChatGPT conversation
→ response_id bound to web conversation

client function_call_output
→ previous_response_id or call_id resolution
→ resume same web conversation
→ send only the new delta
```

If affinity is unavailable, correctness takes priority and the bridge falls back to reconstructed history / persistent Responses continuity.

## Required-tool enforcement

When a request clearly requires a client tool such as `exec_command`, V2 must verify that the Responses output contains a real matching `function_call`. A refusal, a claim that the tool is unavailable, or a text-only answer does not satisfy the contract.

Metadata-only wire observability records:

- request tool names;
- detected required tool;
- function call names;
- argument shape metadata;
- response status and event order.

This is sufficient to distinguish whether a current tool failure originated in the Codex request, UWA tool exposure, required-tool detection or the model response without committing private prompt/tool content.

## Metadata helpers

Codex Desktop/App may issue hidden helper traffic for thread titles or search descriptions. These requests must be classified separately from real coding-agent turns before required-tool detection, main web affinity and authoritative route accounting.

First-release direction:

```text
metadata_helper
→ deterministic bounded local structured response
→ no main ChatGPT coding lane
→ no client-tool requirement
→ no authoritative agent-route update

agent_turn
→ normal UWA web inference/tool protocol
```

## ChatGPT composer send safety

Generic page-wide stop/streaming selectors can produce false positives on an otherwise idle ChatGPT page. The V2 ChatGPT path now gives precedence to a narrowly verified active composer send button when it is visible, enabled, exactly identified as the send control and has no stop/cancel semantics. Ambiguous states retain the conservative existing generation guard.

## Provider and effort routing

UWA mode is expected to use:

```text
provider = uwa
model = chatgpt
default reasoning effort = high
```

Medium and High are supported when the actual request and verified ChatGPT Web state agree. Low/Light is unsupported in UWA mode and fails closed. UI labels alone are not authoritative route evidence.

Official mode restores the signed-in account/provider defaults and must fully stop the repository-owned UWA launcher/listener lifecycle.

## Release path

```text
H3 client-tool exposure + metadata-helper isolation
→ H4/H5 hybrid acceptance
→ one real-project long-task pilot
→ final A-F + compaction + restart regression
→ CI/public-repo safety/docs/license
→ inspect topology
→ merge verified V2 to main
→ standalone extraction S1-S4
```

The standalone repository is created only after the verified `main` baseline. It must preserve required upstream runtime, AGPL-3.0 notices, copyright and explicit attribution.

## Safety

Do not commit browser profiles, cookies, credentials, private logs, full wire traces, Responses SQLite state, live thread/process/browser identifiers, private acceptance prompts, command bodies or tool outputs.
