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
- Responses `function_call -> function_call_output`: PASS
- V2 metadata wire trace: PASS
- V2 strict required-tool repair can produce a real `exec_command`: PASS
- V2 duplicate required-tool suppression after `function_call_output`: PASS
- V2 call-id tool-result continuation affinity: PASS
- V2 single-tool / single-web-conversation gate: PASS

## Latest live acceptance

Stage B `failure_recovery` completed the full audited red-to-green loop in `/Users/jerson/uwa-codex-acceptance`.

Observed sequence:

```text
workspace guard: PASS
initial audited test run: FAIL, exit 1
failure_recovery/.run_history first entry: 1
Codex read parser.py and test_parser.py
only failure_recovery/parser.py was edited
same audited command rerun: PASS, exit 0
failure_recovery/.run_history last entry: 0
independent harness checker: ACCEPTANCE_PASS
```

The implementation change normalized surrounding whitespace before digit/range validation. Tests were not modified.

The shell text-replay seen immediately after this run was not a Codex/UWA process loop. The operator command had assigned the Stage B text to zsh's special `PROMPT` variable. `ps` showed no live `codex exec`; `exec zsh -l` restored the shell. Future operator commands use names such as `ACCEPTANCE_PROMPT` and must not assign zsh special variables such as `PROMPT`, `PS1` or `PATH`.

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

Stage C `git_diff` is NEXT.

Required Stage C evidence:

```text
workspace guard succeeds
initial git_diff tests are red
Codex reads git_diff/REQUIREMENTS.txt
only git_diff/config.py is modified for this scenario
tests pass
git diff --check passes
git diff -- git_diff shows only the intended implementation change
independent checker passes
```

The acceptance workspace intentionally keeps prior Stage A/B implementation evidence. Before Stage C, operator-only noise such as `PROMPTS.md` drift and `__pycache__` directories must be cleaned because the Stage C checker treats them as unexpected paths.

## Acceptance order

```text
Stage A multi-file read/edit/test        PASS
Stage B failure recovery                 PASS
Stage C Git diff discipline              NEXT
Stage D long process + write_stdin       pending
Stage E same-thread context              pending
Stage F Codex + UWA restart              pending
```

After those, run long-context and advanced-tool coverage before treating V2 as production-ready.

## Remaining engineering work

Beyond the Stage C-F acceptance matrix, remaining planned work includes:

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

## Public repository safety

Never commit browser profiles, cookies, local storage, tokens, private prompts/source, UWA logs, wire traces, SQLite continuation state or Codex memory workspace content.
