# Codex Desktop Web Bridge progress

Checkpoint: 2026-09-06
Branch: `security-hardening`

This file records implementation history and current gaps. For a concise handoff, read `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md` first.

## Current target

```text
Codex Desktop
-> Responses-compatible request
-> UWA on localhost
-> ChatGPT Web
-> GPT-5.6 Sol / High
-> web model chooses local client tools
-> UWA emits function_call
-> Codex executes locally
-> function_call_output returns through UWA
-> repeat until task completion
```

The browser page never receives direct filesystem access. Local execution remains governed by Codex sandbox and approval rules.

## Verified milestones

### Bridge basics

- hardened localhost launcher
- isolated controlled Chromium profile
- `/health` and model catalog
- OpenAI Chat Completions compatibility
- OpenAI Responses compatibility
- Responses SSE streaming
- Codex 0.153+ model catalog compatibility
- Codex CLI custom provider inference
- Codex Desktop custom `uwa` provider
- ordinary Desktop text inference

### GPT-5.6 Sol / High path

Real macOS testing confirms the current Codex UI path is running with the intended `GPT-5.6 Sol` label and `High` reasoning state.

Temporary Chat is still attempted, but current ChatGPT DOM does not expose that state consistently enough for it to remain a blocking requirement. It is best-effort unless `UWA_CODEX_TEMPORARY_CHAT_STRICT=true` is explicitly enabled.

### Workspace-tool refusal repair

Real failures showed that a normal web model can see declared client tools yet still answer with phrases equivalent to:

- cannot access local files
- local workspace is not mounted
- `exec_command` is unavailable
- user should run the shell command manually

The bridge now has bounded repair logic that treats these claims as invalid when client workspace tools are actually declared. The repair stays fail-closed and does not overwrite genuine tool results such as file-not-found or permission failures.

### Minimal Codex Responses function-call stream

A major compatibility fix replaced the generic event-by-event Chat Completions translation for tool-capable Codex turns with a conservative Responses SSE path:

```text
response.created
response.output_item.done(function_call)
response.completed
```

This matched the shape expected by Codex's client tool path and enabled real local execution.

### Real single-file acceptance — PASS

A deliberately broken `calc.py` was successfully:

1. read through Codex local tooling;
2. corrected by the model/tool loop;
3. written on the local filesystem;
4. tested with a real assertion;
5. confirmed with `PASS`.

### Real multi-file Stage A — PASS

The generated acceptance workspace required changes in two implementation files while tests remained untouched.

Codex Desktop successfully:

1. inspected the multi-file package;
2. corrected arithmetic implementation errors;
3. corrected a formatting implementation error;
4. ran the actual unittest suite;
5. finished only after all three tests passed.

The independent checker returned:

```text
multi_file: PASS
ACCEPTANCE_PASS
```

This establishes that the bridge is no longer limited to the minimal `calc.py` case.

## Live acceptance matrix

```text
single-file calc.py                    PASS
Stage A multi-file read/edit/test      PASS
Stage B fail/diagnose/repair/rerun     pending
Stage C Git-aware discipline           pending
Stage D long process + write_stdin     pending
Stage E same-thread context            pending
Stage F Codex + UWA restart context    pending
```

The canonical procedure is in `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md` and the fixture generator/checker is `tools/codex_desktop_acceptance.py`.

## Continuation and memory

### Generic Responses state before this checkpoint

The generic Responses adapter stores `previous_response_id` history in Python memory:

```text
max entries = 1024
TTL         = 3600 seconds
```

That process-local state disappears when UWA restarts.

### Private Codex continuation store

The Codex-specific path now has a private SQLite fallback implemented in `app/services/codex_responses_state.py`.

Default location:

```text
~/.uwa/codex_responses.sqlite3
```

Default retention policy:

```text
TTL                 7 days
max entries         4096
max record size     8 MiB
parent mode         0700 where supported
DB/WAL/SHM mode     0600 where supported
```

The store may contain prompts, source snippets and tool output. It must never be committed, uploaded or used as public debugging evidence.

Normal in-process continuation still uses the existing memory store. The private DB is consulted only after the process-local `previous_response_id` is absent or expired. When private state is also missing, a sufficiently complete client replay can be used; delta-only tool turns still fail closed.

Local metadata endpoint:

```text
GET /v1/codex/continuity
```

It returns counts/retention metadata only, not conversation content or the local database path.

### Project-level handoff

Long-term project status is intentionally stored in Git-tracked docs instead of relying on model/account memory:

- `README.md`
- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md`
- this progress file
- Draft PR #1 timeline

A fresh assistant or fresh Codex thread should reconstruct current state from those files plus `git status`, recent commits and relevant test results.

## Current safety posture

- API binds to `127.0.0.1` by default
- CORS disabled
- debug disabled
- remote access disabled
- unsafe Python command-engine capability disabled
- automatic self-update disabled
- DevTools remains local-only
- local Codex sandbox/approval remains authoritative
- `.env`, browser profile, logs, continuation DBs and runtime state are not committed
- public CI includes high-confidence secret/runtime-state checks
- live acceptance fixtures are synthetic and isolated from real projects

## Current known gaps

### 1. Stage B-C normal coding workflow depth

The bridge has passed multi-file editing, but still needs explicit proof of:

- observing a real failing test first;
- using stderr/stdout to repair;
- rerunning successfully;
- maintaining clean Git diff discipline.

### 2. Long-running process continuation

`write_stdin` / persistent command sessions are not yet live-verified through the web bridge.

### 3. Same-thread continuity

Same-thread conversational continuity still needs the synthetic token test.

### 4. Restart continuity

The private continuation store is implemented and covered by automated tests, but a full live test must still:

```text
send context_1
-> quit Codex Desktop
-> restart UWA
-> reopen same Codex thread
-> send context_2 without repeating token
-> verify local artifact
```

This is Stage F. Do not claim restart continuity is complete until it passes.

### 5. Token and context accounting

Web responses still do not provide trustworthy API token accounting. Context indicators should be treated as approximate until local estimation and larger-window stability tests are added.

### 6. Advanced Codex tools

Still pending independent acceptance:

- MCP
- namespace tools
- plugins
- hosted search
- multi-agent
- parallel tool calls
- auxiliary model request behavior

## Immediate next sequence

1. wait for CI on private continuation changes;
2. run Stage B;
3. run Stage C;
4. run Stage D;
5. run Stage E;
6. restart UWA + Codex and run Stage F;
7. update this file, README, current-state doc and PR after every live result.

## Repository-history note

The repository retains its existing license and Git history. Current README and active design docs are written for this fork's Codex web-bridge architecture and acceptance process rather than reproducing the previous project's feature-tour documentation.
