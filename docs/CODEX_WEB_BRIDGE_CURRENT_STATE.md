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
- Stage B attempt 1 still proved `exec_command` delivery and tool-result continuation; the attempt itself was invalid because the selected execution context could not see the synthetic acceptance workspace
- Stage B attempt 2 proved several consecutive `exec_command` deliveries and follow-up tool-result turns in the correct synthetic workspace; the run then stopped because the web model falsely claimed that the currently callable tool list did not contain `exec_command`
- localhost security defaults and public-repository safety scan

## Stage B live issue and current fix

The second Stage B run reached a later multi-round failure. UWA emitted multiple real `exec_command` calls and Codex returned tool results, so the bridge and workspace were active. The final web-model reply nevertheless said that the currently callable client tools did not contain `exec_command`.

Two policy gaps were found:

1. the Chinese refusal pattern did not cover wording such as `当前实际可调用工具中没有名为 exec_command 的客户端工具`;
2. post-tool contradiction repair still depended on the latest user-shaped message looking like a workspace request, but Codex follow-up turns may encode tool output as the newest user item.

The current branch fixes both. Once a real workspace tool call exists in history and the current request still declares that tool, a later explicit claim that the tool is absent is treated as a contradiction regardless of the newest user-item shape. Exact Chinese/English callable-tool-list absence wording is covered, repeated repair becomes stricter, and repeated false claims still fail closed when the retry budget is exhausted.

Regression coverage: `tests/test_client_tool_policy_repeated_refusal.py`.

Latest CI for this policy fix: run #105, all jobs passed.

## Live acceptance still pending

- Stage B rerun with the repeated-tool-absence fix
- Stage C: Git-aware change discipline
- Stage D: long-running process + stdin continuation / `write_stdin`
- Stage E: same-thread conversational continuity
- Stage F: fully quit/reopen Codex + restart UWA + reopen same thread
- larger context windows and compaction
- MCP / namespace tools / plugins / multi-agent
- auxiliary Codex model request optimization

## ChatGPT web-conversation churn

A Codex agent task can create several ChatGPT sidebar conversations today. This is currently expected from the generic UWA workflow, not evidence that Codex Desktop created duplicate tasks.

Current behavior:

```text
one Codex Responses tool turn
-> one reconstructed ChatGPT web request
-> generic workflow prefers a fresh ChatGPT conversation
-> tool result returns to Codex
-> next Responses turn creates another reconstructed web request
```

Internal workspace-repair retries also run additional browser rounds. During the Stage B live run this produced several similar ChatGPT sidebar entries and repeatedly uploaded roughly 45-50k characters of reconstructed context.

Why this is not being fixed by globally enabling page reuse: the current outer-turn payload contains reconstructed full history. Reusing the same ChatGPT conversation while sending that full history again would duplicate context inside the web conversation.

Planned safe optimization order:

1. reuse the current ChatGPT conversation for bounded internal repair rounds, because those are corrections to the immediately preceding web reply;
2. add Codex tool-loop web-session affinity and send only the incremental new tool result / continuation payload when the mapped web conversation is healthy;
3. fall back to a fresh conversation plus full reconstructed history after UWA/browser restart, mapping loss, explicit isolation, or unhealthy page state;
4. keep Git/project checkpoint and private Responses state independent from browser-chat persistence.

Until that optimization lands, multiple ChatGPT sidebar chats are a known efficiency/UX limitation, not a correctness requirement.

## Acceptance workspace discipline

Live acceptance uses a synthetic local repository. A stale Codex project selection can make a valid client `exec_command` execute in the wrong workspace even while the UWA bridge itself is functioning.

The harness has two scenario-scoped gates:

```bash
python3 tools/codex_desktop_acceptance.py prepare --scenario <name>
python3 tools/codex_desktop_acceptance.py preflight --scenario <name>
```

`prepare` recreates only the selected scenario and preserves other scenario results. If the marked acceptance workspace is completely missing, it recreates the full synthetic fixture safely. `preflight` verifies the marker, local Git root, target scenario and expected initial red/clean state.

Action prompts also require a client-side marker check. When the active Codex workdir is wrong, the expected result is:

```text
ACCEPTANCE_WORKSPACE_MISMATCH
```

The model must stop there instead of probing unrelated absolute paths or switching to some other execution environment.

Stage B additionally records actual test exit codes in the synthetic scenario's `.run_history`. The checker requires the first audited test run to be non-zero and the final one to be zero, so the stage cannot pass from final green state alone.

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

- `README.md` - current design, supported path, security defaults and roadmap
- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md` - concise handoff and exact current status
- `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md` - acceptance matrix and verified stages
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md` - implementation history and known gaps
- Draft PR #1 - chronological live-test checkpoints

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

1. rerun Stage B with the repeated-tool-absence policy fix;
2. if Stage B passes, update the acceptance checkpoint immediately;
3. live-test Stage C;
4. live-test Stage D;
5. live-test Stage E;
6. explicitly run Stage F with a full Codex + UWA restart;
7. optimize ChatGPT web-session churn with repair-round reuse first, then safe incremental tool-loop continuation;
8. only after A-F are classified, move to context/token accounting and advanced tools.

## Project-history note

The repository keeps its existing license and commit history. This fork's README and active design documentation describe the current Codex web-bridge architecture and do not reuse the previous project's feature-tour documentation.
