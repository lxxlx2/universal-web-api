# Codex Web Bridge current state

Last updated: 2026-09-06
Branch: `security-hardening`

This file is the canonical handoff for the current project state. Future work should read this file, `README.md`, and `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md` before changing the bridge.

## Goal

Use Codex Desktop / Codex CLI as the local coding client while routing model reasoning through the controlled ChatGPT web session. Local filesystem, shell, tests, Git, sandbox and approval remain Codex-side capabilities.

Target path:

```text
Codex Desktop
-> OpenAI Responses-compatible request
-> UWA on 127.0.0.1:8199
-> controlled ChatGPT Web tab
-> GPT-5.6 Sol / High
-> web model chooses client tools
-> UWA emits Responses function_call
-> Codex executes locally
-> function_call_output returns through UWA
-> repeat until completion
```

## Live verified

- Codex Desktop loads custom `uwa` provider
- ordinary text inference through ChatGPT Web
- GPT-5.6 Sol UI label with High reasoning in the tested web session
- workspace-refusal detection and bounded repair
- minimal Codex Responses SSE function-call delivery
- real `exec_command` execution on macOS
- real function-call output continuation
- single-file `calc.py` read/edit/test loop
- multi-file Stage A acceptance
  - two implementation files modified
  - tests untouched
  - three real unit tests passed
  - generated checker returned `multi_file: PASS` and `ACCEPTANCE_PASS`
- localhost security defaults and public-repository safety scan

## Live acceptance still pending

- Stage B: real failing test -> diagnose -> repair -> rerun
- Stage C: Git-aware change discipline
- Stage D: long-running process + stdin continuation / `write_stdin`
- Stage E: same-thread conversational continuity
- Stage F: fully quit/reopen Codex + restart UWA + reopen same thread
- larger context windows and compaction
- MCP / namespace tools / plugins / multi-agent
- auxiliary Codex model request optimization

## Continuity model

There are three different kinds of state. They must not be conflated.

### 1. Codex Desktop thread history

Codex Desktop visibly keeps prior threads in its own sidebar/history. Closing the app does not modify the project files or Git history. Reopening the SAME thread is the intended way to continue that thread.

This client-side persistence is useful but is not the only project record. We do not rely on it as the canonical source of project status.

### 2. UWA Responses continuation state

The generic Responses adapter historically kept `previous_response_id` state only in Python memory with a one-hour TTL and a maximum of 1024 entries. That state disappears on UWA process restart.

The Codex bridge now adds a private local fallback store:

```text
~/.uwa/codex_responses.sqlite3
```

Default policy:

```text
persistence          enabled
retention            7 days
max entries          4096
max single snapshot  8 MiB
parent permissions   0700 when supported
DB/WAL/SHM mode      0600 when supported
```

The database may contain prompts, source snippets and tool output. It is runtime-private data. Never commit or upload it.

The bridge uses the normal in-memory continuation while it exists. If a `previous_response_id` disappears because UWA restarted or the memory entry expired, the Codex-specific route attempts to restore that conversation snapshot from the private SQLite store. If no persisted state exists but the client supplied a replayable full transcript, it can continue from that transcript. Delta-only tool turns still fail closed when no matching history exists.

Local metadata only:

```bash
curl -sS http://127.0.0.1:8199/v1/codex/continuity | python3 -m json.tool
```

The endpoint does not return stored conversation content or the database path.

### 3. Git-tracked project checkpoint

Long-term project progress belongs in Git, not in model memory.

Canonical tracked files:

- `README.md` — current design, supported path, security defaults and roadmap
- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md` — concise handoff and exact current status
- `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md` — acceptance matrix and verified stages
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md` — implementation history and known gaps
- Draft PR #1 — chronological live-test checkpoints

If a ChatGPT/Codex conversation hits a context limit or a new thread is opened, read these files plus the current Git diff/status before continuing.

## New-thread behavior

A brand-new Codex thread should be treated as a fresh conversational context. Project files and Git state remain unchanged, but model-side conversational details from the old thread are not guaranteed to appear automatically.

For reliable continuation in a new thread:

```text
read README.md
read docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md
read docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md
git status
git log -5 --oneline
inspect relevant diff/tests
continue work
```

Important design decisions must therefore be written to tracked project docs or code/tests, not left only in assistant prose.

## Memory / ChatGPT account personalization

ChatGPT account memory is not used as a project source of truth. Temporary Chat is still requested by the bridge, but current DOM verification of that state is best-effort. The project must remain correct even if no account-level memory is available.

## Security

- API and Chromium DevTools stay loopback-only by default
- no public/LAN DevTools exposure
- unsafe Python command-engine capability stays disabled
- auto-update stays disabled in the hardened workflow
- Codex sandbox and approval remain authoritative for local execution
- private continuation DB, browser profile, logs, cookies and `.env` are never committed
- public docs/tests use synthetic examples only

## Immediate next work

1. complete CI for the private continuation store;
2. live-test Stage B;
3. live-test Stage C;
4. live-test Stage D;
5. live-test Stage E;
6. explicitly run Stage F with a full Codex + UWA restart;
7. only after A-F are classified, move to context/token accounting and advanced tools.

## Project-history note

The repository keeps its existing license and commit history. This fork's README and active design documentation describe the current Codex web-bridge architecture and do not reuse the previous project's feature-tour documentation.
