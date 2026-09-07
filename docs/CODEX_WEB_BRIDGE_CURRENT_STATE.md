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
- Stage B failure recovery: PASS (`ACCEPTANCE_PASS`)
- Stage C Git diff discipline: PASS (`ACCEPTANCE_PASS`)
- Responses `function_call -> function_call_output`: PASS
- V2 metadata wire trace: PASS
- V2 strict required-tool repair can produce a real `exec_command`: PASS
- V2 duplicate required-tool suppression after `function_call_output`: PASS
- V2 call-id tool-result continuation affinity: PASS
- V2 single-tool / single-web-conversation gate: PASS
- client-prefixed Chinese required-tool wording: PASS

## Latest live acceptance

Stage C `git_diff` completed successfully in `/Users/jerson/uwa-codex-acceptance`.

Observed sequence:

```text
workspace guard executed through real exec_command
initial git_diff fixture: red
Codex read git_diff/REQUIREMENTS.txt, config.py and tests
only git_diff/config.py was edited for Stage C
MODE changed dev -> prod
TIMEOUT changed 5 -> 30
tests: 2/2 PASS
git diff --check: PASS
git diff -- git_diff: only git_diff/config.py
REQUIREMENTS.txt/tests unchanged
independent harness checker: ACCEPTANCE_PASS
```

The first Stage C attempt exposed a protocol wording gap: `第一步必须通过客户端 exec_command ...` was not recognized by the strict required-tool detector, allowing ChatGPT Web to answer `ACCEPTANCE_WORKSPACE_MISMATCH` without a real function call. Runtime compatibility now covers client-prefixed Chinese forms such as `必须通过客户端 exec_command` while avoiding ordinary explanatory mentions.

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
- retains structured terminal failure handling and compact failure envelopes;
- recognizes explicit client-prefixed required-tool wording used by the acceptance harness.

## Current live gate

Stage D `interactive` is NEXT.

Required Stage D evidence:

```text
workspace guard succeeds through real exec_command
Codex starts python3 interactive/worker.py as a long-lived process
worker prints READY and remains alive
Codex uses client write_stdin / persistent-process continuation on that same process
GO plus newline is delivered after READY
worker exits and prints INTERACTIVE_PASS
interactive/result.txt contains exactly INTERACTIVE_PASS\n
independent checker passes
```

A one-shot command such as piping `GO` into the worker at launch is not equivalent evidence. Stage D specifically validates process-handle continuity plus `write_stdin` behavior across tool turns.

## Acceptance order

```text
Stage A multi-file read/edit/test        PASS
Stage B failure recovery                 PASS
Stage C Git diff discipline              PASS
Stage D long process + write_stdin       NEXT
Stage E same-thread context              pending
Stage F Codex + UWA restart              pending
```

After those, run long-context and advanced-tool coverage before treating V2 as production-ready.

## Remaining engineering work

Beyond the Stage D-F acceptance matrix, remaining planned work includes:

- successful Responses SSE payload slimming; successful Codex responses can still be large because the full advertised tool set is reflected in terminal payloads;
- ChatGPT Web transcript hygiene so internal adapter/repair prompts are less noisy in the visible conversation;
- session/queue hardening for concurrent Codex requests and controlled-tab contention;
- long-context stress and recovery;
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

## Operator notes

Do not assign acceptance task text to zsh special variables such as `PROMPT`, `PS1` or `PATH`. Use ordinary names such as `ACCEPTANCE_PROMPT`.

The acceptance worktree intentionally preserves prior Stage A/B/C implementation evidence. Clean only operator/test noise such as `PROMPTS.md` drift or `__pycache__` when a checker requires it.

## Public repository safety

Never commit browser profiles, cookies, local storage, tokens, private prompts/source, UWA logs, wire traces, SQLite continuation state or Codex memory workspace content.
