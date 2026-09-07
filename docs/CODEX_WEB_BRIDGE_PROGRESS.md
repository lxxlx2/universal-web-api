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
- `function_call -> function_call_output`: PASS
- V2 metadata wire observability: PASS
- strict required-tool repair reaches a real function call: PASS
- duplicate required-tool suppression after tool output: PASS
- call-id affinity recovery for reconstructed Codex tool-result continuations: PASS
- one real tool execution with one ChatGPT Web conversation: PASS
- synthetic workspace marker/scenario probe: PASS

## V2 problem sequence resolved so far

### 1. Plain text simulated tool output

ChatGPT Web sometimes returned a path such as `/` without a real function call. V2 added a strict required-tool contract and metadata wire trace so simulated output cannot pass as local execution.

### 2. Repeated fresh ChatGPT conversations

The generic UWA workflow could start a fresh web conversation on each Responses/tool/repair round. V2 added response-id web affinity, incremental browser input and a Codex-specific workflow reuse hint.

### 3. Strict repair transport failure

A browser/continuation preparation exception truncated the Codex HTTP/SSE body. Runtime hardening now isolates ancillary failures, buffers protocol events to a terminal boundary and emits structured `response.failed` on internal failure.

### 4. Local hydration failure after web conversation restore

A mapped `/c/...` conversation could already be healthy while local Responses hydration failed. V2 now allows that strict repair to continue as a delta on the already-bound web conversation.

### 5. Duplicate tool execution after `function_call_output`

Live evidence showed Codex could reconstruct the earlier request/call/output history and make the original required-tool request visible again. V2 now treats a matching `function_call + function_call_output` pair as completion of that required-tool obligation.

### 6. Tool-result continuation without usable `previous_response_id`

V2 now supports:

```text
function_call call_id
→ remember call_id -> response_id
→ response_id -> ChatGPT /c/...

function_call_output call_id
→ restore same /c/...
→ send only tool-result delta
```

This path is verified live. The latest workspace probe executed exactly once and completed in the same ChatGPT Web conversation.

## Latest live PASS

```text
/Users/jerson/uwa-codex-acceptance
MARKER=YES
SCENARIO=YES
```

Acceptance properties:

```text
one real exec only
correct Codex cwd
no root workdir override
no duplicate command
same ChatGPT conversation for tool-result continuation
clean final completion
```

## Current next gate

Stage B: `failure_recovery`.

Expected sequence:

```text
initial implementation/test failure
→ Codex observes real failure
→ edits implementation only
→ reruns tests
→ final success
→ preserves run evidence required by the acceptance harness
```

## Remaining acceptance matrix

```text
Stage B failure recovery              NEXT
Stage C Git diff discipline           pending
Stage D long process + write_stdin    pending
Stage E same-thread context           pending
Stage F UWA/Codex restart             pending
```

## Remaining engineering roadmap after B-F

```text
successful Responses SSE payload slimming
ChatGPT Web transcript hygiene
concurrent request / queue / controlled-tab hardening
long-context stress and recovery
advanced MCP/plugin namespace coverage
multi-agent/tool fan-out coverage
lost-affinity fallback and restart recovery
final operator docs and release checklist
```

## Current code checkpoints

```text
1f26fae Stop repeated required tools after Codex tool output
9d38ec1 Cover call-id affinity and one-shot required tools
60689d2 Record V2 call-id continuation fix
```

The live PASS is recorded in current-state/README/PR documentation on the same V2 branch.
