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
- `function_call -> function_call_output`: PASS
- V2 metadata wire observability: PASS
- strict required-tool repair reaches a real function call: PASS
- duplicate required-tool suppression after tool output: PASS
- call-id affinity recovery for reconstructed Codex tool-result continuations: PASS
- one real tool execution with one ChatGPT Web conversation: PASS
- synthetic workspace marker/scenario probe: PASS
- Codex CLI `exec resume` preserves the same thread id across Stage E turns: PASS

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

### 8. Same-thread path-oriented workspace refusal

Stage E turn 1 returned `CONTEXT_READY` and created no file. Turn 2 resumed the exact same Codex thread id, proving client-thread continuity, but ChatGPT Web then claimed that the active execution environment did not contain `/Users/jerson/uwa-codex-acceptance` and performed no local file operation.

The generic workspace-refusal repair already covered mounted/mapped/unavailable wording but did not match this specific Chinese form: `当前可用执行环境中不存在 /Users/...`.

V2 now installs a narrow path-oriented refusal-language compatibility matcher. When the current request is a local workspace task and client workspace tools are declared, this wording is routed through the existing bounded client-workspace repair instead of being accepted as a final answer. Ordinary explanatory path text is not matched.

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

## Stage D verified

Stage D `interactive` passed both the independent checker and the metadata wire-evidence gate.

```text
workspace guard: real exec_command
worker launch: exec_command
worker remained alive waiting for stdin
wire trace: write_stdin function_call observed
write_stdin continuation reused the same ChatGPT Web conversation
worker produced INTERACTIVE_PASS
interactive/result.txt contained INTERACTIVE_PASS
checker: ACCEPTANCE_PASS
```

The terminal UI collapsed the persistent-process interaction into the original `exec` block, so the visible CLI transcript alone was ambiguous. Private metadata trace resolved that ambiguity.

## Current gate

Stage E same-thread context is IN PROGRESS.

First live attempt:

```text
turn 1 thread_id: 01a07b00-4c8b-7822-9aef-bab866d04ffa
turn 1 reply: CONTEXT_READY
turn 1 file state: clean
turn 2 thread_id: same exact id
thread resume: PASS
turn 2 local file action: FAIL due path-oriented workspace refusal
```

Rerun Stage E after the refusal-language repair is pulled and UWA is restarted. PASS still requires the same thread id, recalled `EMBER-7319`, `context/result.txt` containing exactly that token plus newline, and the independent checker passing.

## Remaining acceptance matrix

```text
Stage A multi-file read/edit/test         PASS
Stage B failure recovery                  PASS
Stage C Git diff discipline               PASS
Stage D long process + write_stdin        PASS
Stage E same-thread context               IN PROGRESS
Stage F UWA/Codex restart                 pending
```

## Remaining engineering roadmap after E-F

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
