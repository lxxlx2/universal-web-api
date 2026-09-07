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
- Stage F Codex + UWA restart continuity: PASS
- Responses `function_call -> function_call_output`: PASS
- V2 metadata wire trace: PASS
- strict required-tool repair to a real client tool call: PASS
- duplicate required-tool suppression after `function_call_output`: PASS
- call-id tool-result continuation affinity: PASS
- single-tool / single-web-conversation gate: PASS
- client-prefixed Chinese required-tool wording: PASS
- path-oriented client workspace refusal repair: PASS live rerun

## Latest completed live acceptance

Stage F completed successfully across a real UWA restart.

Verified sequence:

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
same Codex thread resumed after restart: PASS
THREAD_MATCH=YES
context_2 did not repeat the token
real local command execution after restart: PASS
context/result.txt content: EMBER-7319\n
assistant reply: CONTEXT_PASS
web affinity after resume: binding_count=2
independent checker: context: PASS
independent checker: ACCEPTANCE_PASS
```

This proves the workflow survived a real UWA process boundary after process-local affinity was destroyed. Recovery still reached the same Codex thread, recovered conversation-only context, and continued with real client-side local execution.

The live thread identifier and runtime process identifiers remain private and are intentionally excluded from Git.

Detailed records:

- `docs/CODEX_STAGE_E_CONTEXT_WORKSPACE_REFUSAL_2026-09-07.md`
- `docs/CODEX_STAGE_F_RESTART_CONTINUITY_2026-09-07.md`

## Acceptance order

```text
Stage A multi-file read/edit/test        PASS
Stage B failure recovery                 PASS
Stage C Git diff discipline              PASS
Stage D long process + write_stdin       PASS
Stage E same-thread context              PASS
Stage F Codex + UWA restart              PASS
```

## Continuity layers

Current continuity mechanisms are:

1. Codex Desktop / CLI thread history.
2. private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. process-local ChatGPT web-session / call-id affinity.
4. Git tracked handoff documents as the long-term project truth.

Stage F verified that layer 3 disappears across UWA restart while the workflow can still recover through the surviving continuity path and resume real local tools.

## Current engineering priority

The live acceptance foundation is now closed through Stage F. Production hardening continues in this order:

```text
P1 long-context stress and recovery
P1 lost-affinity / restart fallback deeper validation
P1 real-project long-task pilot
P2 concurrent request / queue / controlled-tab hardening
P3 MCP/plugin namespace coverage
P3 multi-agent/tool fan-out coverage
P4 successful Responses SSE payload slimming
P4 ChatGPT Web transcript hygiene
P5 full regression, operator docs and release checklist
```

## Collaboration recording rule

Every completed live stage, important live failure, design change, repair and disruptive-stage checkpoint must be synchronized to Git before the next step. At minimum update README, this canonical handoff, progress tracking, and the stage-specific record.

## Merge policy

Keep `codex-web-bridge-v2` as the active development branch until required stability coverage, real-project pilot, final regression, CI, documentation and public-repository safety checks pass. Then merge the verified branch into `main`.

## Public repository safety

Do not commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, SQLite continuation state, live Codex thread identifiers, local process identifiers, Codex memory workspace content, or private project source captured during acceptance.
