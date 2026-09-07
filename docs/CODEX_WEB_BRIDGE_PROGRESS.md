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

## Stage B verified

Stage B `failure_recovery` passed the independent acceptance checker.

Live evidence:

```text
initial audited test exit: 1
.run_history first entry: 1
implementation edit: failure_recovery/parser.py only
final audited test exit: 0
.run_history last entry: 0
checker: ACCEPTANCE_PASS
```

The parser fix strips surrounding whitespace before digit/range validation. Test files were unchanged.

A repeated block of Stage B text after completion was traced to the operator assigning the prompt text to zsh's special `PROMPT` variable. No `codex exec` process remained. Future commands must use `ACCEPTANCE_PROMPT` or another ordinary variable name.

## Current gate

Stage C `git_diff` is NEXT.

Expected sequence:

```text
prepare synthetic git_diff fixture
→ preflight confirms initial red
→ workspace guard
→ read git_diff/REQUIREMENTS.txt
→ modify git_diff/config.py only for this scenario
→ tests pass
→ git diff --check passes
→ git diff -- git_diff shows only intended implementation change
→ independent checker passes
```

Before Stage C, remove acceptance-workspace noise that the checker does not allow, specifically tracked `PROMPTS.md` drift and untracked `__pycache__` directories. Preserve Stage A/B implementation evidence and `failure_recovery/.run_history`.

## Remaining acceptance matrix

```text
Stage A multi-file read/edit/test         PASS
Stage B failure recovery                  PASS
Stage C Git diff discipline               NEXT
Stage D long process + write_stdin        pending
Stage E same-thread context               pending
Stage F UWA/Codex restart                 pending
```

## Remaining engineering roadmap after C-F

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
ec0e60b Mark V2 single-web tool loop verified
```

Stage B PASS and the Stage C operator gate are recorded in current-state/README/PR documentation on the same V2 branch.
