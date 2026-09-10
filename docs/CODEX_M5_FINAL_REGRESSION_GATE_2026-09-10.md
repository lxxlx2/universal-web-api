# M5 final regression gate — 2026-09-10

## Purpose

M5 is the final composite regression gate before release-safety review. It validates the accepted M4 branch plus the release-blocking native remote-compaction lifecycle correction found during the 2026-09-10 reference-project scan.

M5 does not expand product scope and does not use the official Codex provider.

## One-shot runner

```text
tools/codex_m5_final_regression_safe.py
```

The safe runner delegates to `tools/codex_m5_final_regression.py` after resolving the local validation environment. Production requirements intentionally do not include `pytest`; if the selected runtime-capable Python lacks pytest, the safe wrapper installs pytest only into private `~/.uwa` validation state and leaves the repository and production requirements untouched.

The M5 flow is validation-only with respect to the repository. It does not edit repository files, stage changes, commit, push, reset, restore, switch providers or consume official Codex quota.

## Preconditions

```text
branch                    codex-web-bridge-v2
repository worktree       clean
configured provider       uwa
configured model          chatgpt
configured effort         high
Codex CLI                 available
Stage A-F workspace       present and guarded
M4 implementation         present in branch history
remote-compaction fix     present in branch history
```

M5 fails closed if any precondition is not met.

## Deterministic regression block

The runner executes the existing aggregate acceptance checker against the already-proven Stage A-F workspace:

```text
python3 tools/codex_desktop_acceptance.py check
```

Required result:

```text
ACCEPTANCE_PASS
```

It then selects a repository-capable Python interpreter and runs the complete current `tests/test_codex_*.py` regression family. Before execution, the runner requires the release-critical test files for remote compaction, post-compaction recovery, auto-compaction, restart/lost-affinity fallback, identity fencing, uncertain tool-effect retry safety, route auditing, provider switching, metadata-helper isolation, ordinary stream cancellation and native remote-compaction stream cancellation.

This block revalidates the current implementation for:

```text
legacy Responses compact compatibility
native remote-V2 compaction contract
exactly-one-compaction output behavior
post-compaction recovery orchestration
native auto-compact trigger logic
Responses state/stream compatibility
lost-affinity and restart fallback
continuation identity fencing
uncertain tool-effect reconciliation
provider and route auditing
metadata-helper isolation
ordinary V2 stream cancellation cleanup
native remote-compaction cancellation cleanup
```

M5 does not grow another 57k-token live compaction thread. Native remote V2 compaction and same-thread post-compaction recovery already have decisive M1 live evidence; the post-M4 native-compaction change is limited to lifecycle cleanup and summary instruction hardening. The current compaction regression family plus CI revalidates that narrow delta without delaying the release with redundant context growth.

## Fresh restart-continuity live block

The runner performs a real final-code restart smoke with a guarded synthetic workspace under the user's private UWA state directory and a runtime-generated conversation-only token. The token, raw prompts, raw Codex output and thread identifier are never printed or committed.

Sequence:

```text
restart UWA from the current checkout
prove current UWA health
write a fresh route-audit marker
start a fresh Codex/UWA thread that remembers only the runtime token
require exact seed reply and zero tool activity
verify the token did not leak into the synthetic workspace
restart UWA again to remove process-local affinity
resume the exact Codex thread
require real local exec_command workspace guard
require a second real exec_command that writes and reads the remembered token
verify exact result bytes independently
verify the resumed turn completed
verify authoritative route is uwa / chatgpt / high
verify request-manager returns to zero and browser remains connected
remove the private synthetic workspace on success
```

The second restart is intentional. It ensures the final code can recover through persisted/reconstructed continuation after process-local Web affinity is lost, while the official Codex client still owns the real local tool execution.

## Local validation bootstrap

The first live M5 attempt stopped before any correctness regression because the original interpreter probe required `pytest` together with runtime imports. `requirements.txt` does not include pytest, so a valid runtime Python was rejected solely for lacking the development test dependency.

The safe wrapper now separates runtime capability from test-runner availability. It first requires a Python that imports the project runtime. If pytest is absent, it bootstraps pytest into private `~/.uwa/m5-validation-deps` state and uses a local launcher that adds only that private dependency target to `PYTHONPATH` for M5 validation.

Record: `docs/CODEX_M5_LOCAL_VALIDATION_BOOTSTRAP_2026-09-10.md`.

## Pass contract

M5 closes only when the runner reaches all of the following classes of evidence:

```text
M5_STAGE_A_F_AGGREGATE=PASS
M5_CODEX_REGRESSION=PASS
M5_PY_COMPILE=PASS
M5_FIRST_RESTART=PASS
M5_SEED_TURN=PASS
M5_SECOND_RESTART=PASS
M5_RESTART_CONTINUITY=PASS
M5_REAL_CLIENT_TOOL_ACTIVITY=YES
M5_ROUTE_UWA_CHATGPT_HIGH=YES
M5_REQUEST_MANAGER_CLEAN_AFTER=YES
M5_REPOSITORY_STILL_CLEAN=YES
M5_FINAL_REGRESSION=PASS_LIVE_CLOSED
```

Any failure leaves M5 open and must be classified before M6 begins.

## Release path after M5

```text
M1   PASS / CLOSED
M2   PASS / CLOSED
M3a  PASS / LIVE / CLOSED
M3b  PASS / LIVE / CLOSED
M4   PASS / LIVE / CLOSED
M5   CURRENT
M6   CI + public safety + docs/provenance/license
M7   topology inspection + merge verified V2 to main
```
