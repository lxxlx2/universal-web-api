# Codex Desktop live acceptance

This document tracks the real macOS acceptance of the hardened Codex Desktop -> UWA -> ChatGPT Web bridge.

## Current live results

- minimal single-file `calc.py` read/edit/test loop: **PASS**
- Stage A multi-file read/edit/test: **PASS** on 2026-09-06
- Stage B failure recovery: **rerun required** after an invalid workspace-mismatch attempt
- Stage C Git-aware change discipline: pending
- Stage D long-running process + stdin continuation: pending
- Stage E same-thread context continuity: pending
- Stage F Codex/UWA restart continuity: pending

Stage A is considered passed only because the generated checker returned:

```text
multi_file: PASS
ACCEPTANCE_PASS
```

The assistant's final prose is not used as proof.

## Safety boundary

Use only the generated acceptance workspace for these scenarios. Do not point experimental prompts at a real project until the relevant stage passes.

`tools/codex_desktop_acceptance.py setup` creates `~/uwa-codex-acceptance` by default. It refuses to delete or reset an existing directory unless that directory contains the harness marker file. The fixture contains no credentials or user-specific paths and initializes its own local Git repository.

The bridge remains subject to Codex Desktop sandbox/approval controls. Browser-side ChatGPT does not receive direct filesystem access; local execution remains client-side.

## Setup and scenario preflight

Create the acceptance workspace once:

```bash
python3 tools/codex_desktop_acceptance.py setup
```

Before every live stage, reset only that synthetic scenario and verify it locally:

```bash
python3 tools/codex_desktop_acceptance.py prepare --scenario failure_recovery
python3 tools/codex_desktop_acceptance.py preflight --scenario failure_recovery
```

`prepare` preserves the other scenario directories. If the entire acceptance workspace is missing, it safely recreates the marked synthetic workspace. `preflight` verifies the marker, Git root and target scenario. For deliberately failing test scenarios it also proves the fixture starts red before Codex is asked to act.

Then open the printed acceptance root as the Codex Desktop project. Each action-oriented live prompt now begins with a client-side workspace guard:

```text
pwd
+ marker exists
+ target scenario directory exists
```

If that guard fails, the model must return `ACCEPTANCE_WORKSPACE_MISMATCH` and must not probe unrelated absolute paths or switch to a different execution environment.

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

## Stage A: multi-file read/edit/test - PASS

Goal: prove that the single-file `calc.py` success generalizes to several implementation files and several tool rounds.

Verified behavior:

1. inspected `multi_file/`;
2. modified two implementation files;
3. left tests unchanged;
4. ran the real unittest suite;
5. all three tests passed;
6. the generated checker returned `ACCEPTANCE_PASS`.

Pass command:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario multi_file
```

## Stage B: failure -> diagnose -> repair -> rerun

Goal: prove the agent can observe an actual failing command, use returned stderr/stdout as context, change the implementation, and rerun the same command successfully.

### Attempt 1 classification

The first Stage B attempt on 2026-09-06 is **invalid**, not a bridge failure and not a Stage B pass/fail result.

Evidence from the UWA log:

```text
[CODEX_RESPONSES] ... tool_names=['exec_command']
```

The tool call was delivered to Codex and a real tool result came back on the next Responses turn. That result reported that the intended synthetic acceptance workspace was unavailable in the active execution context. The web model then correctly refused to claim a repair or successful test.

This showed that the bridge's tool round-trip still worked, while the live acceptance setup did not guarantee the selected Codex project matched the synthetic fixture. The harness was therefore hardened with `prepare`, `preflight`, the marker check and `ACCEPTANCE_WORKSPACE_MISMATCH`.

### Machine-auditable failure recovery

Stage B now uses the same unittest command twice through an audited shell wrapper. Each invocation appends its real exit code to:

```text
failure_recovery/.run_history
```

The generated prompt contains the exact audited command. The checker requires all of the following:

1. current tests are green;
2. `.run_history` has at least two recorded runs;
3. the first recorded exit code is non-zero;
4. the last recorded exit code is zero;
5. no non-integer evidence was injected;
6. the only tracked change under `failure_recovery/` is `failure_recovery/parser.py`.

This means a plausible final answer or a manually pre-fixed implementation cannot pass Stage B without evidence of a real failing run followed by a real successful rerun.

For the rerun, execute:

```bash
python3 tools/codex_desktop_acceptance.py prepare --scenario failure_recovery
python3 tools/codex_desktop_acceptance.py preflight --scenario failure_recovery
python3 tools/codex_desktop_acceptance.py prompts --scenario failure_recovery
```

The external preflight only proves that the fixture exists and starts red; it does not write `.run_history` and does not count as the Stage B execution evidence.

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

Goal: verify that a second Codex turn can rely on a fact supplied in the first turn even though UWA creates fresh browser conversations internally and reconstructs context from Responses/Codex history.

Send `context_1`, wait for `CONTEXT_READY`, then send `context_2` in the same Codex Desktop thread. The first prompt forbids writing the token to disk, so the second turn cannot recover it from the fixture.

Pass command:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario context
```

## Stage F: close/reopen Codex + restart UWA continuity

Goal: verify the actual user workflow that matters for long projects.

Procedure:

1. prepare a fresh context scenario so `context/result.txt` does not exist;
2. open a fresh Codex Desktop thread in the acceptance project;
3. send the `context_1` prompt and wait for `CONTEXT_READY`;
4. fully quit Codex Desktop;
5. stop and restart UWA;
6. reopen Codex Desktop;
7. reopen the SAME Codex thread from Desktop history;
8. send `context_2` without repeating the token;
9. run the context checker.

Pass command:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario context
```

This stage exercises both Codex Desktop's own persisted thread history and UWA's private Responses continuation store. It must pass before restart continuity is considered reliable.

## Result classification

A scenario is `PASS` only when the generated local artifact/test confirms the action. A plausible assistant message is not evidence of success.

A run with the wrong or missing acceptance workspace is `INVALID` and must be rerun after `prepare` + `preflight`; it does not count against the bridge implementation.

If a scenario fails, capture the UWA log beginning at the relevant `[CHAT:ENTRY]`, `[CODEX_CONTINUITY]`, or `[CODEX_RESPONSES]` line through the terminal event. Do not publish logs containing private source code, account data, cookies, tokens, or real conversation identifiers.

## After these stages

If A-C pass, the bridge is suitable for guarded normal coding work in disposable or branched worktrees. If D also passes, long-running interactive developer commands are usable. If E passes, same-thread conversational continuity is usable. If F passes, closing/reopening Codex and restarting UWA can be treated as a supported continuation workflow.

Separate future acceptance remains for large-context compaction, MCP/plugins, namespace tools, multi-agent behavior, and auxiliary Codex model requests.
