# Codex Desktop D1 live gate — 2026-09-08

## Goal

Prove the first mandatory Desktop scenario through the actual ChatGPT/Codex Desktop Codex UI on macOS while the managed UWA provider is active.

D1 is intentionally narrow. It proves a real Desktop local-tool round trip before any same-thread or restart behavior is tested.

## Safety boundary

Use only the marked synthetic workspace `~/uwa-codex-acceptance`. Do not use a production/private repository for D1.

Do not restart UWA during D1. Do not re-run the UWA provider switch because the current remote-compaction capability shim must remain enabled. The Desktop application itself is fully restarted before the live turn so it reads the current Codex configuration.

Do not run another Codex/CLI task in parallel with D1 because the private metadata-trace time window is used to associate UWA evidence with this scenario.

## Preconditions

Before the Desktop turn, verify:

```text
model_provider="uwa"
model="chatgpt"
model_reasoning_effort="high"
model_auto_compact_token_limit_scope="body_after_prefix"
UWA_PROVIDER_NAME=Azure
UWA_BASE_URL=http://127.0.0.1:8199/v1
UWA_REQUIRES_OPENAI_AUTH=false
REMOTE_COMPACTION_COMPAT=ENABLED
health service=healthy
browser_connected=true
wire trace mode=metadata
```

A precondition failure stops D1. Do not repair several things at once; record the exact failure first.

## Fixture

Reset the marked synthetic acceptance workspace with `tools/codex_desktop_acceptance.py setup`, then run the `multi_file` preflight.

Required preflight result:

```text
PREFLIGHT_EXPECTED_RED scenario=multi_file
PREFLIGHT_PASS scenario=multi_file
```

The generated prompt requires the model to:

1. use the real client `exec_command` for a workspace guard;
2. inspect `multi_file`;
3. modify at least two implementation files;
4. leave tests unchanged;
5. run the real unittest suite;
6. report the result only after local execution.

## Desktop procedure

Fully quit any existing ChatGPT/Codex Desktop process and reopen the Desktop app without changing provider configuration or restarting UWA.

In the actual Desktop UI:

1. select Codex;
2. open `~/uwa-codex-acceptance` as the project/workspace;
3. start a fresh Codex thread;
4. paste the exact generated `multi_file` prompt;
5. approve only local actions that stay inside the marked acceptance workspace;
6. wait for the task to finish;
7. do not send another Desktop message before collecting D1 evidence.

If an approval attempts an unrelated absolute path, private UWA/Codex store, or another repository, stop and classify D1 as failed rather than approving it.

## Machine-auditable PASS criteria

All conditions are mandatory:

```text
actual Desktop Codex UI was used                         YES
initial multi_file preflight was RED                     YES
post-run checker: multi_file: PASS                       YES
post-run checker: ACCEPTANCE_PASS                        YES
git diff --check                                         exit 0
changed multi_file implementation files                 math_ops.py + summary.py
test files modified                                      NO
new UWA metadata trace records in D1 window              YES
real exec_command function_call in D1 trace              YES
completed Responses turn in D1 trace                     YES
```

The trace evidence must stay metadata-only. Do not print or commit full request bodies, prompts, command bodies, tool output, browser conversation ids, local process ids, account identifiers or private trace filenames.

## Result handling

The operator pastes only the sanitized terminal result plus the Desktop final answer if useful. The next collaborator classifies the result, records the D1 live checkpoint to Git, and only then proceeds to D2.
