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
- Stage F pre-restart turn 1 baseline: PASS
- Stage F real UWA process restart: PASS
- Stage F process-local web affinity cleared: PASS
- Stage F same-thread post-restart resume: PASS
- Stage F real local tool execution after restart: PASS
- Stage F assistant `CONTEXT_PASS`: PASS
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

Stage E initially failed because the web model claimed that the current execution environment did not contain the local synthetic acceptance workspace before a real local tool check. The policy matcher was extended narrowly and the final live rerun passed.

## Current gate

Stage F Codex + UWA restart continuity is IN PROGRESS with only the independent checker remaining.

### Stage F verified chain

```text
prepare context fixture: PASS
preflight context fixture: PASS
fresh Codex thread created: PASS
turn 1 assistant reply: CONTEXT_READY
context/result.txt after turn 1: ABSENT
UWA stopped cleanly: PASS
listener after stop: absent
UWA restarted with a different process: PASS
health after restart: healthy
web affinity before restart: binding_count=4
web affinity after restart: binding_count=0
persistent=false
fallback=fresh_chat_plus_reconstructed_history
same-thread post-restart resume: PASS
THREAD_MATCH=YES
context_2 did not repeat token
real local command execution after restart: PASS
context/result.txt == EMBER-7319\n
assistant: CONTEXT_PASS
affinity after resume: binding_count=2
```

The in-process web affinity layer was destroyed and recovery still succeeded through the surviving continuity path. The real thread identifier and process identifiers remain private and are not written into Git.

Detailed record: `docs/CODEX_STAGE_F_RESTART_CONTINUITY_2026-09-07.md`.

## Remaining acceptance matrix

```text
Stage A multi-file read/edit/test         PASS
Stage B failure recovery                  PASS
Stage C Git diff discipline              PASS
Stage D long process + write_stdin        PASS
Stage E same-thread context               PASS
Stage F Codex + UWA restart               IN PROGRESS
  pre-restart turn 1                      PASS
  UWA restart                             PASS
  process-local affinity cleared          PASS
  same-thread post-restart resume         PASS
  real local execution                    PASS
  CONTEXT_PASS                             PASS
  independent checker                     NEXT
```

## Recording discipline

Every live stage result and disruptive-stage checkpoint must be committed before the next step. README, canonical current state, this progress file, and the stage-specific record stay aligned.

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
