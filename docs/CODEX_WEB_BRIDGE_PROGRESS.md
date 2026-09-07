# Codex Web Bridge Progress

## Branches

- stable verified base: `security-hardening`
- active V2 development: `codex-web-bridge-v2`
- V2 Draft PR: #2

## Verified macOS milestones

- ChatGPT Web inference through UWA: PASS
- Codex custom provider: PASS
- GPT-5.6 Sol / High: PASS
- real `exec_command`: PASS
- native Codex cwd inheritance: PASS
- single-file coding loop: PASS
- Stage A multi-file coding loop: PASS
- Stage B failure recovery: PASS
- Stage C Git diff discipline: PASS
- Stage D long process + `write_stdin`: PASS
- Stage E same-thread context continuity: PASS
- `function_call -> function_call_output`: PASS
- V2 metadata wire observability: PASS
- strict required-tool repair reaches a real function call: PASS
- duplicate required-tool suppression after tool output: PASS
- call-id affinity recovery for reconstructed Codex tool-result continuations: PASS
- one real tool execution with one ChatGPT Web conversation: PASS
- synthetic workspace marker/scenario probe: PASS

## Problem sequence resolved so far

### Plain-text simulated tool output

The bridge now requires real Responses function calls when the client tool is explicitly required. Plausible assistant text cannot satisfy local-execution acceptance.

### Web conversation churn during tool loops

V2 added Responses-to-web affinity and incremental continuation so a client tool round can continue the already-bound ChatGPT conversation where possible.

### Tool-result continuation without usable previous_response_id

V2 supports the reconstructed-history shape through metadata-only `call_id -> response_id` recovery and reuses the corresponding web conversation when available.

### Duplicate required-tool execution

A matching `function_call + function_call_output` pair marks that obligation complete, preventing the original request from forcing the same tool repeatedly.

### Client-prefixed required-tool language

Acceptance wording such as `第一步必须通过客户端 exec_command ...` is treated as an explicit real-tool requirement.

### Root workdir override

A generated `workdir="/"` is removed when the user did not explicitly request filesystem root, preserving the native Codex turn cwd.

### Same-thread path-oriented workspace refusal

Stage E initially failed because the web model claimed that the current execution environment did not contain `/Users/jerson/uwa-codex-acceptance` before a real local tool check.

The policy matcher was extended to cover this narrow path-missing refusal form. Regression coverage verified conversion to a real `exec_command` call without guessed `workdir`.

The final live rerun then passed:

```text
thread_id turn 1 == thread_id turn 2
THREAD_MATCH=YES
turn 2 was not given EMBER-7319 again
real local exec_command ran in /Users/jerson/uwa-codex-acceptance
context/result.txt contained EMBER-7319\n
assistant: CONTEXT_PASS
checker: context: PASS
checker: ACCEPTANCE_PASS
```

Stage E is therefore closed as PASS.

## Current gate

Stage F Codex + UWA restart continuity is NEXT.

This gate must verify that the same Codex thread remains usable after the local client workflow and UWA are restarted. Process-local web affinity is expected to be gone, so recovery must rely on Codex thread history, persisted Responses state, and the documented reconstructed-history fallback.

## Remaining acceptance matrix

```text
Stage A multi-file read/edit/test         PASS
Stage B failure recovery                  PASS
Stage C Git diff discipline              PASS
Stage D long process + write_stdin        PASS
Stage E same-thread context               PASS
Stage F Codex + UWA restart               NEXT
```

## Recording discipline

Every live stage result must be committed before the next stage begins. README, canonical current state, this progress file, and the stage-specific record must stay aligned. This is required for multi-agent and multi-conversation collaboration where any one chat may reach its context limit.

## Roadmap after Stage F

```text
successful Responses SSE payload slimming
ChatGPT Web transcript hygiene
concurrent request / queue / controlled-tab hardening
long-context stress and recovery
advanced MCP/plugin namespace coverage
multi-agent/tool fan-out coverage
lost-affinity fallback validation
real-project long-task pilot
full Stage A-F regression
final operator docs
release checklist
```

## Final merge plan

The active V2 branch will be merged into `main` only after the required live gates, stability checks, real-project pilot, final regression, CI and repository-safety checks are green and the handoff documentation is current.
