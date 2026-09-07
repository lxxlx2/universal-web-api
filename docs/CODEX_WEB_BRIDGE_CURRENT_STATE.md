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
- Stage A multi-file read/edit/test: PASS (`ACCEPTANCE_PASS`)
- Responses `function_call -> function_call_output`: PASS
- V2 metadata wire trace: PASS
- V2 strict required-tool repair can produce a real `exec_command`: PASS
- V2 duplicate required-tool suppression after `function_call_output`: PASS
- V2 call-id tool-result continuation affinity: PASS
- V2 single-tool / single-web-conversation gate: PASS

## Latest live acceptance

The workspace probe executed exactly once:

```text
/bin/zsh -lc 'pwd && printf "MARKER=" && test -f .uwa_codex_acceptance && echo YES || echo NO && printf "SCENARIO=" && test -d failure_recovery && echo YES || echo NO' in /Users/jerson/uwa-codex-acceptance
```

Real output:

```text
/Users/jerson/uwa-codex-acceptance
MARKER=YES
SCENARIO=YES
```

The turn then completed normally. There was no second execution of the command and no new ChatGPT Web conversation for the tool-result continuation.

The preceding minimal `pwd` acceptance also proved the full call-id fallback path:

```text
remembered function call ids for same-web-conversation tool-result continuation
required client tool already has a matching function_call_output; suppressing duplicate enforcement
reusing ChatGPT conversation from function_call_output call_id
trimmed reconstructed Responses history to function_call_output delta for web-session reuse
```

The final browser continuation completed with `web_session_reused=True`, `browser_input=delta`, and no second function call.

## V2 continuation design now verified

Two continuation shapes are supported:

```text
A. previous_response_id continuation
response_id -> ChatGPT /c/...
```

and the live Codex reconstructed-history shape:

```text
B. function_call_output continuation
call_id -> response_id -> ChatGPT /c/...
```

The second shape can contain the original user request, earlier `function_call`, and `function_call_output`. A matching call/output pair marks that required-tool obligation complete, so the original request cannot force the same tool twice.

Runtime hardening now:

- recognizes completed `function_call + function_call_output` pairs and suppresses duplicate required-tool enforcement;
- remembers process-local metadata-only `call_id -> response_id` mappings when UWA emits a function call;
- uses that call id to recover the already-bound ChatGPT conversation when Codex returns tool output without a usable UWA `previous_response_id`;
- trims reconstructed history to the new `function_call_output` delta before sending it to the reused web conversation;
- stores only call ids, response ids and timestamps in this map; no prompt, command text or tool result text is stored;
- retains degraded same-conversation repair when local Responses hydration fails;
- retains structured terminal failure handling and compact failure envelopes.

## Current live gate

Stage B `failure_recovery` is now IN PROGRESS.

The harness first resets only the synthetic `failure_recovery` fixture, verifies that its tests are initially red and that `.run_history` does not exist, then sends the canonical Stage B prompt to a fresh Codex turn.

Required Stage B evidence:

```text
workspace guard succeeds
initial audited test run fails for real
first non-zero exit code is appended to failure_recovery/.run_history
Codex reads the failure and edits only failure_recovery/parser.py
same audited test command is rerun until green
last exit code in .run_history is 0
independent checker passes
```

The harness also rejects unexpected tracked changes under `failure_recovery`; only `failure_recovery/parser.py` may be modified. `.run_history` is allowed as the audit artifact and must not be deleted or rewritten.

## Acceptance order

```text
Stage B failure recovery             IN PROGRESS
Stage C Git diff discipline          pending
Stage D long process + write_stdin   pending
Stage E same-thread context          pending
Stage F Codex + UWA restart          pending
```

After those, run long-context and advanced-tool coverage before treating V2 as production-ready.

## Remaining engineering work

Beyond the Stage B-F acceptance matrix, remaining planned work includes:

- successful Responses SSE payload slimming; successful Codex responses can still be large because the full advertised tool set is reflected in terminal payloads;
- ChatGPT Web transcript hygiene so internal adapter/repair prompts are less noisy in the visible conversation;
- session/queue hardening for concurrent Codex requests and controlled-tab contention;
- long-context stress and recovery;
- `write_stdin` and long-running shell processes;
- MCP/plugin/tool namespace coverage;
- multi-agent/tool fan-out coverage;
- restart and lost-affinity fallback validation;
- final README/operator documentation and release checklist.

## Continuity

Long-term project truth remains Git tracked docs and code. Additional runtime continuity layers are:

- Codex Desktop thread history;
- private UWA Responses SQLite state at `~/.uwa/codex_responses.sqlite3`;
- in-process ChatGPT web conversation affinity;
- in-process call-id metadata affinity.

UWA mode keeps Codex automatic Memories disabled during acceptance to avoid background memory jobs contending for the controlled ChatGPT tab.

## Public repository safety

Never commit browser profiles, cookies, local storage, tokens, private prompts/source, UWA logs, wire traces, SQLite continuation state or Codex memory workspace content.
