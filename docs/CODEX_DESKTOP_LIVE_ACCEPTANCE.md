# Codex bridge live acceptance

This document tracks the real macOS acceptance of the hardened Codex -> UWA -> ChatGPT Web bridge.

## Evidence boundary

The core A-F sequence is PASS, but its final Stage E/F evidence was machine-audited primarily through `codex exec` / `codex exec resume`. That proves the Responses protocol, thread continuation, local tool execution and UWA restart path. It must not be treated as completed proof of the ChatGPT Desktop Codex UI itself.

Actual Desktop UI validation is now a separate mandatory gate:

`docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`

That gate must pass before merge to `main`.

## Current live results

```text
minimal single-file read/edit/test        PASS
Stage A multi-file read/edit/test         PASS
Stage B failure recovery                  PASS
Stage C Git-aware change discipline       PASS
Stage D long-running process + stdin      PASS
Stage E same-thread context continuity    PASS
Stage F Codex + UWA restart continuity    PASS
aggregate A-F checker                     PASS
Desktop UI D1-D5                         pending / mandatory
```

Stage F final proof crossed a real UWA process boundary, cleared process-local web affinity, resumed the same Codex thread without repeating the context token, executed a real local command, restored the expected context artifact, returned `CONTEXT_PASS`, and passed the independent checker:

```text
context: PASS
ACCEPTANCE_PASS
```

Canonical current state lives in:

- `README.md`
- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`
- `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`
- `docs/CODEX_STAGE_E_CONTEXT_WORKSPACE_REFUSAL_2026-09-07.md`
- `docs/CODEX_STAGE_F_RESTART_CONTINUITY_2026-09-07.md`

## Safety boundary

Use only the generated acceptance workspace for synthetic scenarios. Do not point experimental prompts at private or production source trees until the relevant synthetic gate has passed.

`tools/codex_desktop_acceptance.py setup` creates `~/uwa-codex-acceptance` by default. It refuses to delete or reset an existing directory unless that directory contains the harness marker file. The fixture contains no credentials or user-specific paths and initializes its own local Git repository.

Browser-side ChatGPT does not receive direct filesystem access; local execution remains client-side under Codex sandbox/approval controls.

## Setup and scenario preflight

Create the acceptance workspace once:

```bash
python3 tools/codex_desktop_acceptance.py setup
```

Before a synthetic stage, reset only the selected scenario and verify it locally:

```bash
python3 tools/codex_desktop_acceptance.py prepare --scenario failure_recovery
python3 tools/codex_desktop_acceptance.py preflight --scenario failure_recovery
```

Show prompts:

```bash
python3 tools/codex_desktop_acceptance.py prompts
python3 tools/codex_desktop_acceptance.py prompts --scenario multi_file
```

Check one completed scenario:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario multi_file
```

Check all existing synthetic scenarios:

```bash
python3 tools/codex_desktop_acceptance.py check
```

## Stage A: multi-file read/edit/test — PASS

Goal: prove that the single-file success generalizes to several implementation files and several tool rounds.

Verified behavior: inspected `multi_file/`, modified only intended implementation files, left tests unchanged, ran the real unittest suite, and passed the generated checker.

## Stage B: failure -> diagnose -> repair -> rerun — PASS

Goal: prove the agent can observe an actual failing command, use returned stderr/stdout as context, change the implementation, and rerun the same command successfully.

The final machine-auditable scenario requires a real initial non-zero exit code and a final zero exit code in `failure_recovery/.run_history`, while only the intended implementation file may change.

## Stage C: Git-aware change discipline — PASS

Goal: prove normal repository hygiene without allowing the agent to commit.

Verified behavior includes reading requirements, modifying only intended implementation, running tests, running `git diff --check`, and inspecting the scoped diff while leaving the baseline commit untouched.

## Stage D: long-running command + stdin continuation — PASS

Goal: exercise the client-side persistent process path (`exec_command` followed by the corresponding stdin/continuation tool, normally `write_stdin`).

The synthetic worker printed `READY`, accepted `GO` on stdin, wrote `interactive/result.txt`, printed `INTERACTIVE_PASS`, and the independent checker passed.

## Stage E: same-thread context continuity — PASS

Goal: verify that a second Codex turn can rely on a fact supplied in the first turn.

The first prompt stored `EMBER-7319` only in conversation context. The second prompt did not repeat it. The final rerun resumed the exact same Codex thread, recovered the token, executed real local tools, wrote `context/result.txt`, returned `CONTEXT_PASS`, and passed the independent checker.

Detailed record: `docs/CODEX_STAGE_E_CONTEXT_WORKSPACE_REFUSAL_2026-09-07.md`.

## Stage F: Codex + UWA restart continuity — PASS

Goal: verify the long-project workflow across a UWA restart.

Final verified sequence:

1. prepare fresh `context` fixture;
2. start a fresh Codex thread;
3. send `context_1`, receive `CONTEXT_READY`;
4. allow the first CLI process to exit;
5. stop UWA and verify the listener disappears;
6. restart UWA as a different process;
7. verify `/v1/codex/web-affinity` goes from nonzero bindings to zero after restart with `persistent=false`;
8. resume the same Codex thread;
9. send `context_2` without repeating the token;
10. verify the same thread id;
11. execute a real local command and restore `context/result.txt` as `EMBER-7319\n`;
12. receive `CONTEXT_PASS`;
13. run the independent checker and receive `context: PASS` plus `ACCEPTANCE_PASS`.

Detailed record: `docs/CODEX_STAGE_F_RESTART_CONTINUITY_2026-09-07.md`.

## Desktop UI gate

The final product target includes ChatGPT Desktop in Codex mode. The additional D1-D5 cases cover:

```text
D1 real Desktop local tool/coding round trip
D2 same Desktop thread continuation
D3 full Desktop application restart + history resume
D4 Desktop + UWA double restart + same-thread recovery
D5 clean return to normal signed-in ChatGPT account mode with no hard-coded model
```

Each Desktop case must use the actual UI and still finish with machine-auditable local evidence. See `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`.

## Result classification

A scenario is `PASS` only when a generated local artifact/test confirms the action. Plausible assistant prose or screenshots alone are not proof.

A run with the wrong or missing acceptance workspace is `INVALID` and must be rerun after `prepare` + `preflight`; it does not count against the bridge implementation.

If a scenario fails, inspect the relevant local UWA metadata/log evidence. Do not publish logs containing private source code, account data, cookies, tokens, real conversation identifiers, live process identifiers, or Responses SQLite contents.

## Production-hardening after A-F

```text
P1 Responses compact endpoint compatibility
P1 large-context compaction / recovery
P1 lost-affinity fallback depth
Desktop UI D1-D5
real-project long-task stability
MCP/plugins and namespace tools
multi-agent behavior
concurrent request / queue / controlled-tab behavior
ChatGPT web-session churn and transcript hygiene
successful Responses SSE payload slimming
full regression and release checklist
```

The current synthetic target is **Responses compact protocol support**, followed by large-context compaction/recovery. Desktop D1-D5 must then pass before the real-project/final merge gate.
