# Codex Web Bridge current state

Canonical handoff for the `codex-web-bridge-v2` branch.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while routing model inference through UWA to logged-in ChatGPT Web. Codex remains the local executor for filesystem, shell, edits, tests, Git, sandbox and approval.

## Verified live capabilities

- ordinary UWA / ChatGPT Web inference: PASS
- Codex custom provider: PASS
- GPT-5.6 Sol / High target path: PASS
- real Codex `exec_command`: PASS
- Codex native turn cwd inheritance: PASS
- single-file read/edit/test: PASS
- Stage A multi-file read/edit/test: PASS
- Stage B failure recovery: PASS
- Stage C Git diff discipline: PASS
- Stage D long process + `write_stdin`: PASS
- Stage E same-thread context continuity: PASS
- Stage F pre-restart turn 1 baseline: PASS
- Stage F real UWA restart: PASS
- Stage F process-local affinity cleared after restart: PASS
- Responses `function_call -> function_call_output`: PASS
- V2 metadata wire trace: PASS
- strict required-tool repair to a real client tool call: PASS
- duplicate required-tool suppression after `function_call_output`: PASS
- call-id tool-result continuation affinity: PASS
- single-tool / single-web-conversation gate: PASS
- client-prefixed Chinese required-tool wording: PASS
- path-oriented client workspace refusal repair: PASS live rerun

## Latest completed live acceptance

Stage E completed successfully in the synthetic acceptance workspace. Its final same-thread rerun recovered the conversation-only token without repeating it, performed real local tool calls, returned `CONTEXT_PASS`, and passed the independent checker.

Detailed Stage E record:

`docs/CODEX_STAGE_E_CONTEXT_WORKSPACE_REFUSAL_2026-09-07.md`

## Current live gate

Stage F Codex + UWA restart continuity is IN PROGRESS.

Verified so far:

```text
fresh context fixture prepared: PASS
context preflight: PASS
fresh Codex thread created: PASS
turn 1 reply: CONTEXT_READY
context/result.txt after turn 1: ABSENT
real UWA stop: PASS
UWA listener absent after stop: PASS
UWA restarted as a different process: PASS
health after restart: healthy
web affinity before restart: binding_count=4
web affinity after restart: binding_count=0
web affinity persistence: false
fallback: fresh_chat_plus_reconstructed_history
private turn-1 JSONL remains present
context/result.txt after restart: ABSENT
```

This is the critical proof that Stage F crossed a real UWA process boundary. Process-local ChatGPT web-session and call-id affinity are gone in the new process, while the acceptance fixture remains untouched.

The live thread identifier and runtime process identifiers are intentionally kept out of the public repository. They are recovered only from local private state when needed for the resume step.

Next required sequence:

```text
recover the same Stage F thread id locally
generate context_2 from the acceptance harness
send context_2 through codex exec resume without repeating the token
require the same thread id on resume
require real local tool execution
require context/result.txt == EMBER-7319\n
require CONTEXT_PASS
require independent context checker ACCEPTANCE_PASS
```

Do not reset or prepare the context fixture between Stage F turn 1 and turn 2.

Detailed Stage F record:

`docs/CODEX_STAGE_F_RESTART_CONTINUITY_2026-09-07.md`

## Acceptance order

```text
Stage A multi-file read/edit/test        PASS
Stage B failure recovery                 PASS
Stage C Git diff discipline              PASS
Stage D long process + write_stdin       PASS
Stage E same-thread context              PASS
Stage F Codex + UWA restart              IN PROGRESS
  pre-restart turn 1                     PASS
  UWA restart                            PASS
  process-local affinity cleared         PASS
  same-thread post-restart resume        NEXT
  independent checker                    pending
```

## Continuity layers

Current continuity mechanisms are:

1. Codex Desktop / CLI thread history.
2. private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. process-local ChatGPT web-session / call-id affinity.
4. Git tracked handoff documents as the long-term project truth.

Stage F has now verified that layer 3 really disappears across a UWA restart. The next resume must therefore succeed through the remaining continuity mechanisms and documented reconstructed-history fallback as needed.

## Collaboration recording rule

Every completed live stage, important live failure, design change, repair and disruptive-stage checkpoint must be synchronized to Git before the next step. At minimum update README, this canonical handoff, progress tracking, and the stage-specific record. This allows another collaborator to continue solely from the repository when a chat session reaches its context limit.

## Remaining engineering work after Stage F

- successful Responses SSE payload slimming
- ChatGPT Web transcript hygiene
- concurrent request / queue / controlled-tab hardening
- long-context stress and recovery
- MCP/plugin namespace coverage
- multi-agent/tool fan-out coverage
- lost-affinity fallback validation
- real-project long-task pilot
- full acceptance regression
- final operator docs and release checklist

## Merge policy

Keep `codex-web-bridge-v2` as the active development branch until Stage F, required stability coverage, final regression, CI, documentation and public-repository safety checks pass. Then merge the verified branch into `main`.

## Public repository safety

Do not commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, SQLite continuation state, live Codex thread identifiers, local process identifiers, Codex memory workspace content, or private project source captured during acceptance.
