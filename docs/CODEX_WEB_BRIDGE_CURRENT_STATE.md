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
- Responses `function_call -> function_call_output`: PASS
- V2 metadata wire trace: PASS
- strict required-tool repair to a real client tool call: PASS
- duplicate required-tool suppression after `function_call_output`: PASS
- call-id tool-result continuation affinity: PASS
- single-tool / single-web-conversation gate: PASS
- client-prefixed Chinese required-tool wording: PASS
- path-oriented client workspace refusal repair: PASS live rerun

## Latest live acceptance

Stage E completed successfully in `/Users/jerson/uwa-codex-acceptance`.

Observed sequence:

```text
turn 1 stored EMBER-7319 only in conversation context
turn 1 left context/result.txt absent
turn 2 resumed the exact same Codex thread id
turn 2 was not given EMBER-7319 again
real exec_command inspected the acceptance workspace
context/result.txt was written as EMBER-7319\n
file was read back successfully
assistant returned CONTEXT_PASS
independent checker returned context: PASS
independent checker returned ACCEPTANCE_PASS
```

Stage E initially exposed a false path-oriented workspace refusal. The policy matcher was extended narrowly, covered by regression tests, pulled into the live environment, and the final same-thread rerun passed.

Detailed record:

`docs/CODEX_STAGE_E_CONTEXT_WORKSPACE_REFUSAL_2026-09-07.md`

## Current live gate

Stage F Codex + UWA restart continuity is NEXT.

Stage F must prove the real long-running project workflow:

```text
prepare a fresh context fixture
start a fresh Codex thread
turn 1 stores the context token and returns CONTEXT_READY
fully stop Codex Desktop / CLI client session as required by the procedure
stop and restart UWA
resume the exact same Codex thread
send turn 2 without repeating the token
recover the token from persisted thread / Responses history
perform real local tool execution
write and read context/result.txt
independent checker returns ACCEPTANCE_PASS
```

This gate specifically exercises restart behavior after process-local web affinity has been lost. UWA must recover through Codex thread history plus private persisted Responses state and the documented fresh-chat reconstructed-history fallback where needed.

## Acceptance order

```text
Stage A multi-file read/edit/test        PASS
Stage B failure recovery                 PASS
Stage C Git diff discipline              PASS
Stage D long process + write_stdin       PASS
Stage E same-thread context              PASS
Stage F Codex + UWA restart              NEXT
```

## Continuity layers

Current continuity mechanisms are:

1. Codex Desktop / CLI thread history.
2. private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. process-local ChatGPT web-session / call-id affinity.
4. Git tracked handoff documents as the long-term project truth.

Process-local web affinity is expected to disappear across a UWA restart. Restart recovery must therefore work without depending on that in-memory map.

## Collaboration recording rule

Every completed live stage, important live failure, design change and repair must be synchronized to Git before the next stage starts. At minimum update README, this canonical handoff, progress tracking, and the stage-specific record. This allows another collaborator to continue solely from the repository when a chat session reaches its context limit.

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

Do not commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, SQLite continuation state, Codex memory workspace content, or private project source captured during acceptance.
