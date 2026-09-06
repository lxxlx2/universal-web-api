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
- Stage B attempt 1 proved `exec_command` delivery and tool-result continuation but was invalid because the selected execution context could not see the synthetic acceptance workspace
- Stage B attempt 2 proved several consecutive `exec_command` deliveries and follow-up tool-result turns, then exposed a false post-tool claim that `exec_command` was absent
- a later clean CLI probe proved the Codex turn cwd itself was correct while the web-generated tool call still executed from `/`, isolating an accidental root `workdir` override
- localhost security defaults and public-repository safety scan

## Stage B policy fixes

Two earlier policy gaps were fixed:

1. Chinese/English claims such as `当前实际可调用工具中没有名为 exec_command 的客户端工具` are recognized as contradictions after a real tool call has already succeeded.
2. Post-tool contradiction repair no longer depends on the newest user-shaped item still resembling the original coding request, because Codex follow-up turns may encode tool output as that newest item.

Regression coverage: `tests/test_client_tool_policy_repeated_refusal.py`.

## Root workdir diagnosis and current fix

A clean CLI probe was launched from `~/uwa-codex-acceptance`. Codex itself reported the correct turn workdir:

```text
workdir: /Users/jerson/uwa-codex-acceptance
provider: uwa
model: chatgpt
```

The user required a real `exec_command` containing only `pwd`, but the actual tool output was `/`.

Official Codex inherits the turn environment cwd when `exec_command.workdir` is omitted. The observed result therefore isolates the failure to the web-generated tool arguments overriding the client cwd with `workdir: "/"`.

Current guard:

1. for `exec_command`, `shell_command`, and `local_shell`, `/` is rejected as an implicit/default workdir unless the user explicitly requested filesystem root;
2. the internal repair preserves the intended command and requires the corrected call to omit `workdir` entirely;
3. UWA never guesses an absolute replacement path;
4. repeated root forcing fails closed after the bounded retry budget;
5. explicit root requests remain allowed.

Regression coverage: `tests/test_client_tool_policy_root_workdir.py`.

Detailed checkpoint: `docs/CODEX_ROOT_WORKDIR_FIX_2026-09-06.md`.

CI run #115 passed all jobs, including full regression and public-repository safety.

## Live acceptance still pending

- rerun the minimal CLI `pwd` probe after the root-workdir guard
- Stage B failure-recovery rerun only after that probe returns the acceptance workspace path
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

Internal workspace-repair retries also run additional browser rounds. During Stage B this produced several similar ChatGPT sidebar entries and repeatedly uploaded large reconstructed contexts.

Why this is not being fixed by globally enabling page reuse: outer-turn payloads currently contain reconstructed full history. Reusing the same ChatGPT conversation while sending that full history again would duplicate context inside the web conversation.

Planned safe optimization order:

1. reuse the current ChatGPT conversation for bounded internal repair rounds;
2. add Codex tool-loop web-session affinity and send only incremental new tool result / continuation payloads when the mapped web conversation is healthy;
3. fall back to fresh chat + full reconstructed history after UWA/browser restart, mapping loss, explicit isolation, or unhealthy page state;
4. keep Git/project checkpoint and private Responses state independent from browser-chat persistence.

Until that optimization lands, multiple ChatGPT sidebar chats are a known efficiency/UX limitation, not a correctness requirement.

## Acceptance workspace discipline

Live acceptance uses a synthetic local repository. The harness has two scenario-scoped gates:

```bash
python3 tools/codex_desktop_acceptance.py prepare --scenario <name>
python3 tools/codex_desktop_acceptance.py preflight --scenario <name>
```

`prepare` recreates only the selected scenario and preserves other scenario results. `preflight` verifies the marker, local Git root, target scenario and expected initial red/clean state.

Action prompts also require a client-side marker check. When the active Codex workdir is wrong, the expected result is:

```text
ACCEPTANCE_WORKSPACE_MISMATCH
```

The model must stop there instead of probing unrelated absolute paths or switching to a different execution environment.

Stage B additionally records actual test exit codes in `.run_history`. The checker requires the first audited test run to be non-zero and the final one to be zero.

## Codex automatic Memories isolation

Live testing showed that Codex can start background memory-consolidation work after a foreground task completes. Under the custom provider those requests also entered UWA, consumed the single controlled ChatGPT tab and generated extra web chats.

Until dedicated acceptance is complete, UWA mode disables:

```toml
[memories]
generate_memories = false
use_memories = false
```

Helper:

```bash
python3 tools/codex_uwa_memory_guard.py status
python3 tools/codex_uwa_memory_guard.py disable
python3 tools/codex_uwa_memory_guard.py restore
```

This does not delete existing Codex threads, project files, Git state, existing memory files, or the UWA continuation database.

## Continuity model

There are three different kinds of state. They must not be conflated.

### 1. Codex Desktop thread history

Codex Desktop visibly keeps prior threads in its own sidebar/history. Closing the app does not modify project files or Git history. Reopening the SAME thread is the intended way to continue that thread.

### 2. UWA Responses continuation state

The Codex bridge adds a private local fallback store:

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

The database may contain prompts, source snippets and tool output. It is runtime-private data and must never be committed.

Local metadata only:

```bash
curl -sS http://127.0.0.1:8199/v1/codex/continuity | python3 -m json.tool
```

### 3. Git-tracked project checkpoint

Long-term project progress belongs in Git, not in model memory.

Canonical tracked files:

- `README.md`
- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`
- `docs/CODEX_UWA_MEMORIES.md`
- `docs/CODEX_ROOT_WORKDIR_FIX_2026-09-06.md`
- Draft PR #1

If a ChatGPT/Codex conversation hits a context limit or a new thread is opened, read these files plus current Git diff/status before continuing.

## New-thread behavior

A brand-new Codex thread should be treated as a fresh conversational context. Project files and Git state remain unchanged, but model-side conversational details from the old thread are not guaranteed to appear automatically.

For reliable continuation:

```text
read README.md
read docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md
read docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md
git status
git log -5 --oneline
inspect relevant diff/tests
continue work
```

## Memory / ChatGPT account personalization

ChatGPT account memory is not used as a project source of truth. Temporary Chat remains best-effort. The project must remain correct even if no account-level memory is available.

## Security

- API and Chromium DevTools stay loopback-only by default
- no public/LAN DevTools exposure
- unsafe Python command-engine capability stays disabled
- auto-update stays disabled in the hardened workflow
- Codex sandbox and approval remain authoritative for local execution
- private continuation DB, browser profile, logs, cookies and `.env` are never committed
- public docs/tests use synthetic examples only

## Immediate next work

1. pull/restart UWA and rerun the minimal CLI `exec_command(pwd)` probe;
2. require `/Users/.../uwa-codex-acceptance`, not `/`, before Stage B resumes;
3. rerun Stage B and update the acceptance checkpoint immediately if it passes;
4. live-test Stage C, then D, E, F;
5. optimize ChatGPT web-session churn with repair-round reuse first, then safe incremental tool-loop continuation;
6. only after A-F are classified, move to context/token accounting and advanced tools.

## Project-history note

The repository keeps its existing license and commit history. This fork's README and active design documentation describe the current Codex web-bridge architecture and do not reuse the previous project's feature-tour documentation.