# Codex Web Bridge Progress

## Branches

- stable verified base: `security-hardening`
- active V2 development: `codex-web-bridge-v2`
- V2 Draft PR: #2

## Verified milestones

```text
Stage A-F protocol/CLI acceptance                    PASS
aggregate A-F checker                                PASS
P1.1 legacy Responses compact direct live            PASS
versioned lifecycle/provider switch CI/live          PASS
P1.2 native auto-compact + remote V2 compaction      PASS / LIVE
P1.2 same-thread post-remote recovery                 PASS / CLOSED
P1.3 minimal continuity blockers                     PASS / CLOSED
ChatGPT idle-composer send repair                     PASS / LIVE / CLOSED
Desktop D1-D5                                        PASS / LIVE / CLOSED
Hybrid H0-H5                                         PASS / LIVE / CLOSED
M3a Hybrid Routing Safety                            PASS / LIVE / CLOSED
M3b Desktop UI                                       PASS / LIVE / CLOSED
```

## M3a final acceptance

The one-shot hybrid finalizer completed successfully on 2026-09-10. H3 preserved the official source effect exactly once and appended the UWA continuation exactly once; a real client tool call occurred; authoritative route was `uwa / chatgpt / high`; metadata helpers were excluded from agent accounting; H4 private ledger and H5 aggregate acceptance passed; request-manager returned to zero.

Canonical live record: `docs/CODEX_HYBRID_M3A_LIVE_PASS_2026-09-10.md`.

## Current gate: M4 focused cancellation repair

The first M4 long turn was real and non-trivial but did not finish inside the harness wall-clock bound.

```text
preflight route                              uwa / chatgpt / high
preflight health                             running=0 / browser connected
route marker                                 PASS
Codex elapsed                                719 seconds
Codex event classes                          thread.started, turn.started, item.started, item.completed
real tool items                              14
stream disconnect                            absent
workspace after timeout                      only app/api/codex_responses_v2.py modified
post-timeout request-manager                 0
post-timeout browser                         connected
```

The deterministic recovery path then reached the focused async-stream regression layer:

```text
ignored baseline handling                    PASS
repository-capable Python selection           PASS
canonical cancellation patch target           unique
canonical implementation written              YES
regression test written                       YES
py_compile                                    PASS
normal completion regression                  PASS
explicit aclose regression                    FAIL
consumer cancellation regression              FAIL
```

The detailed diagnostic isolated the failures.

`test_aclose_cleans_backing_task_after_keepalive` failed because it required the literal substring `keepalive` but the observed non-terminal transport event was `response.in_progress`. This is an overconstrained test assumption for the lifecycle behavior M4 is validating.

`test_consumer_cancellation_cleans_backing_task` confirmed the backing worker received cancellation, but the workflow reuse hint was still true at the assertion point. The focused implementation repair therefore clears the reuse hint immediately on unwind before the cancellation-sensitive await, then cancels and awaits the backing task. The consumer test also uses a long heartbeat interval to remove a heartbeat/cancellation race while still requiring caller `CancelledError` propagation.

The one-shot closer is now:

```text
tools/codex_m4_focused_repair_and_close.py
```

It performs safe resume-state checks, UWA readiness, the focused implementation/test rewrite, three deterministic stdlib regressions, `py_compile`, `git diff --check`, one bounded read-only Codex/UWA review, route and health verification, then commits/pushes only the implementation and regression-test paths if every gate passes.

Do not rerun the original 12-minute long task.

Detailed records:

- `docs/CODEX_M4_LONG_TASK_TIMEOUT_RECOVERY_2026-09-10.md`
- `docs/CODEX_M4_FOCUSED_UNITTEST_FAILURE_2026-09-10.md`
- `docs/CODEX_M4_FOCUSED_REPAIR_2026-09-10.md`

## Accelerated release-critical path

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       PASS / LIVE / CLOSED
M3b Desktop UI D1-D5                                  PASS / LIVE / CLOSED
M4 one real-project long-task pilot                   CURRENT / focused cancellation repair
M5 final A-F + compaction + restart regression        pending
M6 CI green + public-repo safety + docs/provenance    pending
M7 branch-topology inspection + merge to main         pending
```

M4 closes only on `M4_REAL_PROJECT_LONG_TASK_PILOT=PASS_LIVE_CLOSED`.

## Post-main standalone plan

After verified V2 is merged to `main`:

```text
S1 dependency/import/runtime audit + core manifest
S2 create clearer standalone attributed repository
S3 rerun full CI + CLI/Desktop/live parity acceptance
S4 publish first standalone research release
```

The standalone extraction keeps genuinely required upstream runtime and preserves AGPL-3.0 plus explicit attribution while removing unrelated generic fork surface only after dependency proof.

## Current records

- `docs/CODEX_M4_FOCUSED_REPAIR_2026-09-10.md`
- `docs/CODEX_M4_FOCUSED_UNITTEST_FAILURE_2026-09-10.md`
- `docs/CODEX_M4_LONG_TASK_TIMEOUT_RECOVERY_2026-09-10.md`
- `docs/CODEX_M4_REAL_PROJECT_LONG_TASK_GATE_2026-09-10.md`
- `docs/CODEX_HYBRID_M3A_LIVE_PASS_2026-09-10.md`
- `docs/CODEX_DESKTOP_D5_LIVE_PASS_2026-09-09.md`
- `docs/ACCELERATED_MAIN_MERGE_GATE_2026-09-08.md`

## Recording discipline

Every live result, failure, repair and disruptive checkpoint is committed before the next step. README, canonical current state, this file and Draft PR #2 should stay aligned. Public records contain only non-sensitive evidence and omit private prompt/tool bodies, raw account/thread/process/browser identifiers and private trace contents.
