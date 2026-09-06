# Codex Web Bridge current state

Last updated: 2026-09-06
Branch: `security-hardening`

This is the canonical handoff. Future work should read this file, `README.md`, and `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md` before changing the bridge.

## Goal

Use Codex Desktop / CLI as the local coding client while routing model reasoning through a controlled ChatGPT Web session. Filesystem, shell, tests, Git, sandbox and approval remain Codex-side capabilities.

```text
Codex Desktop / CLI
-> Responses-compatible request
-> UWA 127.0.0.1:8199
-> ChatGPT Web
-> GPT-5.6 Sol / High
-> web model chooses declared client tool
-> UWA emits Responses function_call
-> Codex executes locally
-> function_call_output returns through UWA
-> repeat until completion
```

## Live verified

- custom `uwa` provider loads in Codex Desktop and CLI
- ordinary text inference through ChatGPT Web
- GPT-5.6 Sol / High target web mode
- minimal Codex Responses SSE function-call delivery
- real `exec_command` on macOS
- real function-call-output continuation
- single-file read/edit/test loop
- Stage A multi-file acceptance: PASS / `ACCEPTANCE_PASS`
- multiple consecutive `exec_command` rounds have executed successfully
- localhost security defaults and public-repository safety scan

## Current Stage B status

Stage B failure-recovery is still pending live PASS. The important failures found so far have been converted into code, regression tests and public checkpoints.

### 1. False workspace/tool refusal

The web model has emitted claims such as:

```text
current callable tools do not include exec_command
exec_command is unavailable
```

Current policy:

- if a workspace tool is declared, explicit claims that the named declared tool is unavailable are repairable contradictions;
- if a real workspace tool call already exists in history, later claims that the same declared tool disappeared are repaired without relying on the newest user-shaped item still looking like the original coding request;
- explicit user references to `exec_command`, `shell_command`, `local_shell`, `apply_patch`, or `write_stdin` count as local client-tool requests, so minimal probes are covered;
- repair is bounded and fails closed after the retry budget;
- genuine tool errors such as missing files, permission errors and failed tests remain visible.

Regression coverage:

- `tests/test_client_tool_policy.py`
- `tests/test_client_tool_policy_repeated_refusal.py`
- `tests/test_client_tool_policy_root_workdir.py`

### 2. Accidental root workdir override

A clean CLI probe showed Codex's own turn cwd was correct, while the actual `exec_command(pwd)` ran from `/`. This isolated a web-generated `workdir="/"` override.

Current guard:

```text
user did not explicitly request filesystem root
+
exec-like tool proposes workdir="/"
-> reject candidate before delivery to Codex
-> preserve intended command
-> require corrected call to omit workdir
-> Codex inherits its turn cwd
```

UWA does not guess a replacement absolute path. Explicit root requests remain allowed. Repeated root forcing fails closed.

After the first live root guard test, the repair round returned the text `exec_command unavailable` instead of a corrected call. A second policy gap was found: the minimal probe explicitly named `exec_command` but did not contain generic workspace/file keywords. Explicit workspace tool names are now included in local-task detection, and the exact direct-unavailable behavior is covered by regression.

Latest compatibility CI: Security hardening #122, all 6 jobs passed including full upstream regression and public-repository safety.

## Next live gate

Do not run full Stage B until both short CLI probes pass.

Probe 1 must execute `pwd` through real `exec_command` and return the synthetic acceptance workspace, not `/` and not a tool-unavailable message.

Probe 2 must return:

```text
<acceptance-workspace>
MARKER=YES
SCENARIO=YES
```

If both pass, reset and rerun Stage B.

## Acceptance matrix

```text
single-file read/edit/test                 PASS
Stage A multi-file read/edit/test          PASS
Stage B failure recovery                   pending short-probe gate
Stage C Git diff discipline                pending
Stage D long process + write_stdin         pending
Stage E same-thread continuity             pending
Stage F Codex + UWA restart continuity     pending
Codex automatic Memories                   isolated / future dedicated acceptance
```

The synthetic acceptance harness uses:

```bash
python3 tools/codex_desktop_acceptance.py prepare --scenario <name>
python3 tools/codex_desktop_acceptance.py preflight --scenario <name>
python3 tools/codex_desktop_acceptance.py prompts --scenario <name>
python3 tools/codex_desktop_acceptance.py check --scenario <name>
```

Stage B records actual test exit codes in `.run_history`; checker requires first audited run non-zero and final run zero.

## Codex automatic Memories isolation

Codex can start background memory-consolidation after a foreground task. Under the custom provider those requests also entered UWA and competed for the controlled ChatGPT tab.

Until dedicated acceptance is complete, UWA mode uses:

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

This does not delete Codex threads, project files, Git state, existing memory files, or UWA continuation state.

## ChatGPT web-conversation churn

A single Codex agent task can currently generate several similar ChatGPT sidebar conversations. Each outer tool turn reconstructs history and the generic workflow tends to create a fresh ChatGPT conversation. Internal repair can add more browser rounds.

Planned safe optimization:

1. reuse current web conversation for bounded repair rounds;
2. add tool-loop web-session affinity;
3. send incremental tool-result continuation when mapping is healthy;
4. fall back to fresh chat plus reconstructed history after mapping loss/restart/unhealthy state.

Do not globally reuse one page with full reconstructed history, because that would duplicate context.

## Continuity model

Three independent layers:

1. Codex Desktop thread history.
2. UWA private Responses continuation store: `~/.uwa/codex_responses.sqlite3`.
3. Git-tracked project checkpoint.

The continuation DB may contain prompts, code snippets and tool output. It is private runtime state and must never be committed.

Canonical tracked handoff files:

- `README.md`
- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`
- `docs/CODEX_UWA_MEMORIES.md`
- `docs/CODEX_ROOT_WORKDIR_FIX_2026-09-06.md`
- Draft PR #1

New thread recovery:

```text
read README.md
read docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md
read docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md
git status
git log -5 --oneline
inspect relevant diff/tests
continue
```

## Security

- API and Chromium DevTools remain loopback-only by default
- no public/LAN DevTools exposure
- unsafe Python command-engine capability disabled
- auto-update disabled in hardened workflow
- Codex sandbox and approval remain authoritative
- private DB, browser profile, logs, cookies, `.env`, local memory content and private workspace data are never committed
- public docs/tests use synthetic or redacted examples only

## Immediate next work

1. pull latest branch and restart UWA;
2. rerun short CLI `exec_command(pwd)` probe;
3. if it passes, run marker/scenario probe;
4. only then rerun Stage B;
5. immediately record Stage B result in README/current-state/acceptance/PR;
6. continue C, D, E, F;
7. after correctness gates, optimize web-session churn and advanced tools.

## Project history

The repository keeps its existing license and Git commit history. Active README and architecture/acceptance docs describe this fork's own Codex Web Bridge design and maintenance path.