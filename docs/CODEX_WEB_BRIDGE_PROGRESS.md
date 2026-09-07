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

This path is verified live.

### 7. Client-prefixed required-tool wording

Stage C exposed that `第一步必须通过客户端 exec_command ...` could bypass strict tool detection and allow a plain-text workspace mismatch answer. V2 now treats client-prefixed Chinese variants as explicit required-tool requests while leaving ordinary explanatory mentions untouched.

## Stage B verified

Stage B `failure_recovery` passed the independent acceptance checker.

```text
initial audited test exit: 1
.run_history first entry: 1
implementation edit: failure_recovery/parser.py only
final audited test exit: 0
.run_history last entry: 0
checker: ACCEPTANCE_PASS
```

A repeated block of Stage B text after completion was traced to assigning task text to zsh's special `PROMPT` variable. No `codex exec` process remained. Future commands use `ACCEPTANCE_PROMPT`.

## Stage C verified

Stage C `git_diff` passed the independent checker on macOS.

Observed evidence:

```text
workspace guard executed through real exec_command
initial git_diff fixture: red
requirements read: MODE=prod, TIMEOUT=30
implementation edit: git_diff/config.py only
tests: 2/2 PASS
git diff --check: PASS
git diff -- git_diff: only git_diff/config.py
protected REQUIREMENTS.txt/tests: unchanged
checker: ACCEPTANCE_PASS
```

The final acceptance workspace intentionally retains Stage A/B/C implementation evidence:

```text
multi_file/math_ops.py
multi_file/summary.py
failure_recovery/parser.py
failure_recovery/.run_history
git_diff/config.py
```

## Current gate

Stage D `interactive` is NEXT.

The harness expects a real long-lived local process plus stdin continuation:

```text
workspace guard
→ start python3 interactive/worker.py
→ observe READY while process remains alive
→ use client write_stdin / persistent-process tool on the same process
→ send GO plus newline
→ process exits with INTERACTIVE_PASS
→ interactive/result.txt contains INTERACTIVE_PASS
→ independent checker passes
```

A one-shot shell command that pipes `GO` at process launch does not prove Stage D. The goal is to validate that Codex can keep a process handle/session alive across tool turns and then use `write_stdin` against that same process.

## Remaining acceptance matrix

```text
Stage A multi-file read/edit/test         PASS
Stage B failure recovery                  PASS
Stage C Git diff discipline               PASS
Stage D long process + write_stdin        NEXT
Stage E same-thread context               pending
Stage F UWA/Codex restart                 pending
```

## Remaining engineering roadmap after D-F

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
