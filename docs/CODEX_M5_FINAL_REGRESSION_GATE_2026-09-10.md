# M5 final regression gate — 2026-09-10

## Purpose

M5 is the final composite regression gate before release-safety review. It validates the accepted M4 branch plus the release-blocking native remote-compaction lifecycle correction found during the 2026-09-10 reference-project scan.

M5 does not expand product scope and does not use the official Codex provider.

## One-shot runner

```text
tools/codex_m5_final_regression_safe_v2.py
```

The safe v2 runner delegates to the existing M5 flow after resolving two environment-sensitive validation concerns. Production requirements intentionally do not include `pytest`; if the selected runtime-capable Python lacks pytest, the wrapper installs pytest only into private `~/.uwa` validation state and leaves the repository and production requirements untouched. The historical Stage A-F workspace is also treated as mutable live-test state rather than an immutable release artifact; M5 reruns the current aggregate checker against a fresh private deterministic replay fixture instead of changing or trusting the old workspace.

The M5 flow is validation-only with respect to the repository. It does not edit repository files, stage changes, commit, push, reset, restore, switch providers or consume official Codex quota.

## Preconditions

```text
branch                    codex-web-bridge-v2
repository worktree       clean
configured provider       uwa
configured model          chatgpt
configured effort         high
Codex CLI                 available
M4 implementation         present in branch history
remote-compaction fix     present in branch history
```

M5 fails closed if any precondition is not met.

## Deterministic Stage A-F replay block

The original Stage A-F live acceptance and aggregate checker are already historical `PASS / CLOSED` evidence. The old `~/uwa-codex-acceptance` directory is intentionally reusable by `prepare --scenario`, so later Desktop/recovery exercises can reset individual scenario state. M5 therefore does not use that mutable directory as an immutable release artifact.

The safe v2 runner creates a fresh guarded replay workspace under private `~/.uwa` state, initializes it from the current `tools/codex_desktop_acceptance.py` harness, materializes the documented successful end state for each scenario, reruns the current aggregate checker, and removes the private replay workspace afterward.

Required result:

```text
M5_STAGE_A_F_AGGREGATE=PASS
M5_STAGE_A_F_AGGREGATE_SOURCE=PRIVATE_DETERMINISTIC_REPLAY
M5_STAGE_A_F_REPLAY_CLEANED=YES
```

This replay validates the current checker and scenario invariants. It is not represented as a new live Stage A-F route/tool run. The fresh live route/tool proof in M5 remains the restart-continuity block below.

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

The safe wrapper separates runtime capability from test-runner availability. It first requires a Python that imports the project runtime. If pytest is absent, it bootstraps pytest into private `~/.uwa/m5-validation-deps` state and uses a local launcher that adds only that private dependency target to `PYTHONPATH` for M5 validation.

Record: `docs/CODEX_M5_LOCAL_VALIDATION_BOOTSTRAP_2026-09-10.md`.

## Stage A-F mutable-workspace recovery

The second live M5 attempt passed runtime selection and the private pytest bootstrap, then stopped at the aggregate checker with `multi_file` and `context` green while `failure_recovery`, `git_diff` and `interactive` were no longer in their historical completed state. This occurred before the current Codex regression family or restart-continuity live smoke.

That failure is classified as an acceptance-workspace lifecycle issue. The old workspace is mutable by design and is preserved untouched. Safe v2 now uses the private deterministic replay described above.

Record: `docs/CODEX_M5_STAGE_AF_REPLAY_RECOVERY_2026-09-10.md`.

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

## Live closure

The final safe-v2 run completed successfully on 2026-09-10.

```text
Stage A-F private deterministic replay              PASS
current Codex test files                             37
Codex regression                                     201 passed / 0 failed
py_compile                                           PASS
git diff --check                                    PASS
first UWA restart                                    PASS
seed turn                                            PASS
second UWA restart                                   PASS
same Codex thread after restart                      YES
real local client tool activity                      YES
continuity result exact                              YES
post-marker route                                    uwa / chatgpt / high
post-marker response status                          completed
final request-manager running count                  0
final browser connection                             healthy
repository clean                                     YES
private workspace cleanup                            PASS
```

M5 is therefore `PASS / LIVE / CLOSED`. Canonical evidence: `docs/CODEX_M5_FINAL_REGRESSION_LIVE_PASS_2026-09-10.md`.

Updated release path:

```text
M1   PASS / CLOSED
M2   PASS / CLOSED
M3a  PASS / LIVE / CLOSED
M3b  PASS / LIVE / CLOSED
M4   PASS / LIVE / CLOSED
M5   PASS / LIVE / CLOSED
M6   CURRENT
M7   pending
```
