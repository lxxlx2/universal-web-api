# Codex Desktop live acceptance

This document tracks the real macOS acceptance of the hardened Codex Desktop -> UWA -> ChatGPT Web bridge.

The small `calc.py` acceptance has passed live: the browser-backed model produced a client tool call, Codex Desktop executed it on the local workspace, the tool result returned through Responses, the file was changed, and the local assertion passed. The remaining work is to determine how well that loop generalizes to normal coding-agent workflows.

## Safety boundary

Use only the generated acceptance workspace for these scenarios. Do not point experimental prompts at a real project until the relevant stage passes.

`tools/codex_desktop_acceptance.py setup` creates `~/uwa-codex-acceptance` by default. It refuses to delete or reset an existing directory unless that directory contains the harness marker file. The fixture contains no credentials or user-specific paths and initializes its own local Git repository.

The bridge remains subject to Codex Desktop sandbox/approval controls. Browser-side ChatGPT does not receive direct filesystem access; local execution remains client-side.

## Setup

From the `security-hardening` checkout:

```bash
python3 tools/codex_desktop_acceptance.py setup
```

Then open the printed acceptance workspace as a Codex Desktop project.

Show all prompts:

```bash
python3 tools/codex_desktop_acceptance.py prompts
```

Show one prompt:

```bash
python3 tools/codex_desktop_acceptance.py prompts --scenario multi_file
```

Check one completed scenario:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario multi_file
```

Check all scenarios:

```bash
python3 tools/codex_desktop_acceptance.py check
```

## Stage A: multi-file read/edit/test

Goal: prove that the single-file `calc.py` success generalizes to several implementation files and several tool rounds.

Expected behavior:

1. inspect `multi_file/`;
2. modify at least two implementation files;
3. do not modify tests;
4. run the real unittest suite;
5. finish only after the suite is green.

Pass command:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario multi_file
```

## Stage B: failure -> diagnose -> repair -> rerun

Goal: prove the agent can observe an actual failing command, use the returned stderr/stdout as context, change the implementation, and rerun the same command successfully.

The prompt explicitly requires the first test command to fail before editing. This distinguishes genuine failure recovery from a model that simply guesses the intended patch.

Pass command:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario failure_recovery
```

## Stage C: Git-aware change discipline

Goal: prove normal repository hygiene without allowing the agent to commit.

Expected behavior:

1. read `git_diff/REQUIREMENTS.txt`;
2. modify only the intended implementation;
3. run tests;
4. run `git diff --check`;
5. inspect `git diff -- git_diff`;
6. leave the baseline commit untouched.

Pass command:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario git_diff
```

## Stage D: long-running command + stdin continuation

Goal: exercise the client-side persistent process path (`exec_command` followed by the corresponding stdin/continuation tool, normally `write_stdin`).

`interactive/worker.py` prints `READY`, waits for one line on stdin, accepts only `GO`, writes `interactive/result.txt`, prints `INTERACTIVE_PASS`, and exits.

This is deliberately isolated because a failure here should not block ordinary read/edit/test coding workflows.

Pass command:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario interactive
```

## Stage E: same-thread context continuity

Goal: verify that a second Codex turn can rely on a fact supplied in the first turn even though UWA creates fresh browser conversations internally and reconstructs context from the Responses/Codex history.

Send `context_1`, wait for `CONTEXT_READY`, then send `context_2` in the same Codex Desktop thread. The first prompt forbids writing the token to disk, so the second turn cannot recover it from the fixture.

Pass command:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario context
```

## Result classification

A scenario is `PASS` only when the generated local artifact/test confirms the action. A plausible assistant message is not evidence of success.

If a scenario fails, capture the UWA log beginning at the relevant `[CHAT:ENTRY]` or `[CODEX_RESPONSES]` line through the terminal event. Do not publish logs containing private source code, account data, cookies, tokens, or real conversation identifiers.

## After these stages

If A-C pass, the bridge is suitable for guarded normal coding work in disposable/branched worktrees. If D also passes, long-running interactive developer commands are usable. If E passes, same-thread conversational continuity is usable for normal multi-turn tasks.

Separate future acceptance remains for persistent Responses state across UWA restarts, large-context compaction, MCP/plugins, namespace tools, multi-agent behavior, and auxiliary Codex model requests.
