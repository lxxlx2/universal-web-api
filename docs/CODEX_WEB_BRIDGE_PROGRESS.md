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

## V2 problem sequence

### 1. Plain text simulated tool output

ChatGPT Web sometimes returned a path such as `/` without a real function call. V2 added a strict required-tool contract and metadata wire trace so simulated output cannot pass as local execution.

### 2. Repeated fresh ChatGPT conversations

The generic UWA workflow could start a fresh web conversation on each Responses/tool/repair round. V2 added response-id web affinity, incremental browser input and a Codex-specific workflow reuse hint.

### 3. Strict repair transport failure

A browser/continuation preparation exception truncated the Codex HTTP/SSE body. Runtime hardening now isolates ancillary failures, buffers protocol events to a terminal boundary and emits structured `response.failed` on internal failure.

### 4. Local hydration failure after web conversation restore

A mapped `/c/...` conversation could already be healthy while local Responses hydration failed. V2 now allows that strict repair to continue as a delta on the already-bound web conversation.

### 5. Duplicate tool execution after `function_call_output`

Latest live evidence showed the strict repair successfully emitted one real `exec_command`, and Codex executed `pwd` in `/Users/jerson/uwa-codex-acceptance`. The next outer Codex request reconstructed the earlier request/call/output history and V2 forced `exec_command` again, causing a second identical execution.

Current repair:

```text
function_call call_id
→ remember call_id -> response_id
→ response_id -> ChatGPT /c/...

function_call_output call_id
→ restore same /c/...
→ send only tool-result delta
```

A matching `function_call + function_call_output` also marks the explicit required-tool obligation complete, so reconstructed history cannot force it twice.

## Current gate

Run exactly one synthetic `exec_command(pwd)` acceptance turn.

PASS requires:

```text
one real exec only
cwd = /Users/jerson/uwa-codex-acceptance
no second pwd
same ChatGPT conversation after tool output
clean final completion
```

Do not resume Stage B until this passes.

## Pending acceptance

```text
Stage B failure recovery
Stage C Git diff discipline
Stage D long process + write_stdin
Stage E same-thread context
Stage F UWA/Codex restart continuation
```

## Current code checkpoints

```text
1f26fae Stop repeated required tools after Codex tool output
9d38ec1 Cover call-id affinity and one-shot required tools
```

Documentation checkpoints follow those code commits on the same V2 branch.

Security hardening #140 passed the code head, including upstream regression. README/current-state documentation was then updated and remains subject to the same public-repo safety workflow.
