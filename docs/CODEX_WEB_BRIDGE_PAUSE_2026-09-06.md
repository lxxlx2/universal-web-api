# Codex Web Bridge pause checkpoint

Date: 2026-09-06
Branch: `security-hardening`
Status: paused for higher-priority work

## Verified progress

- Codex Desktop and CLI can use the custom `uwa` provider.
- ChatGPT Web GPT-5.6 Sol / High reasoning is reachable through UWA.
- Responses-compatible function-call delivery has worked end to end.
- Real macOS `exec_command` execution and function-call-output continuation have worked.
- Single-file read/edit/test acceptance passed.
- Stage A multi-file read/edit/test passed with `ACCEPTANCE_PASS`.
- Automatic Codex Memories are isolated in UWA mode via `tools/codex_uwa_memory_guard.py`.
- Public-repository security hardening, docs and CI coverage are in place.

## Current blocker at pause

Stage B failure-recovery has not passed yet.

The latest short CLI probe shows this contradictory pair:

```text
Codex turn header workdir: /Users/jerson/uwa-codex-acceptance
Observed final probe text: /
```

Root-workdir policy and Codex Responses boundary sanitization were added and covered by regression. However, the latest live probe still printed `/`.

Important unresolved question at pause: determine whether `/` was a real `exec_command` result or plain web-model text. The next diagnostic should inspect the most recent UWA log for `CODEX_RESPONSES`, `tool_names`, `exec_command`, tool-calling repair and root-workdir lines before changing more cwd logic.

Recommended first command when resuming:

```bash
tail -n 500 ~/.uwa/uwa.log | grep -E 'CODEX_RESPONSES|tool_calling|exec_command|tool_names|root workdir|客户端工作区|函数调用|tool_call'
```

Interpretation:

- `tool_names=['none']`: `/` was likely plain model text, so enforce required client-tool use for explicit `exec_command` requests.
- `tool_names=['exec_command']` with root-workdir stripping: inspect exact Responses delivery / Codex execution semantics.
- `tool_names=['exec_command']` without root override: inspect Codex turn execution environment next.

Do not rerun full Stage B until the short `pwd` probe is proven to be a real client tool call and returns the acceptance workspace.

## Acceptance matrix at pause

```text
single-file read/edit/test                 PASS
Stage A multi-file read/edit/test          PASS
Stage B failure recovery                   BLOCKED on short exec_command probe
Stage C Git diff discipline                pending
Stage D long process + write_stdin         pending
Stage E same-thread continuity             pending
Stage F Codex + UWA restart continuity     pending
Codex automatic Memories                   isolated / future dedicated acceptance
```

## Continuity / handoff

Canonical tracked files:

- `README.md`
- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`
- `docs/CODEX_UWA_MEMORIES.md`
- `docs/CODEX_ROOT_WORKDIR_FIX_2026-09-06.md`
- this pause checkpoint
- Draft PR #1

Private runtime state such as `~/.uwa/codex_responses.sqlite3`, browser profiles, logs, cookies, `.env`, local memory contents and real project data must not be committed.

## Switching away from UWA

Switching Codex back to the official provider does not alter this branch, Git history, acceptance workspace or tracked checkpoints. Stop UWA, restore the official Codex config, and restore original Codex Memories settings if desired. When returning, switch back to UWA and continue from this checkpoint.
