# Accelerated Main Merge Gate — 2026-09-08

## Purpose

Define the narrow release-critical path for merging verified Codex Web Bridge V2 into `main` without allowing broad framework expansion to delay the first stable integration.

## Policy

Only blockers that affect correctness, local execution safety, provider/quality routing, continuity, live Codex Desktop/CLI behavior, public-repository safety or release reproducibility stay in the pre-main gate.

Broad P2-P5 expansion, generalized dashboards, optional runtime research and unrelated upstream cleanup remain post-main unless a live acceptance result proves that one of them is required for correctness.

## Verified baseline

```text
Stage A-F protocol/CLI acceptance                  PASS
aggregate A-F checker                              PASS
P1.1 compact direct live                           PASS
P1.2 stream/usage/TokenCount                       PASS
P1.2 native auto-compact + remote V2 compaction    PASS / LIVE
P1.2 same-thread post-remote recovery              PASS / CLOSED
P1.3 minimal continuity blockers                   PASS / CLOSED
ChatGPT idle-composer send repair                  PASS / LIVE / CLOSED
Hybrid H0-H5                                       PASS / LIVE / CLOSED
M3a Hybrid Routing Safety                          PASS / LIVE / CLOSED
Desktop D1-D5                                      PASS / LIVE / CLOSED
M3b Desktop UI                                     PASS / LIVE / CLOSED
M4 real-project long-task pilot                    PASS / LIVE / CLOSED
remote-compaction cancellation follow-up           PASS / CI
```

## M3a closed

The final synthetic official -> UWA handoff acceptance passed. The official source effect remained exactly once, the UWA continuation effect occurred exactly once, the independent handoff checker passed, a real `exec_command` client tool call occurred, metadata-helper traffic was excluded from agent accounting, authoritative route metadata resolved to `uwa / chatgpt / high`, the private transition ledger passed, and request-manager returned to zero.

Detailed record: `docs/CODEX_HYBRID_M3A_LIVE_PASS_2026-09-10.md`.

## M4 closed

The real-project long-task gate is closed. The accepted implementation in `app/api/codex_responses_v2.py` now guarantees that an unfinished `_run_chat_completion_final` backing task is cancelled and awaited when the outer async stream unwinds, while caller cancellation propagates and normal completion remains unchanged.

M4 closure evidence includes three focused cancellation regressions, `py_compile`, `git diff --check`, a completed bounded real Codex/UWA review, independent real-client-tool proof, authoritative `uwa / chatgpt / high` route evidence, request-manager running count zero and healthy browser state.

Detailed record: `docs/CODEX_M4_REAL_PROJECT_LONG_TASK_LIVE_PASS_2026-09-10.md`.

The 2026-09-10 reference-project scan found the same orphan-task class on the separate native remote-compaction V2 worker path. That release blocker has also been corrected with unconditional pending-worker cancel/await cleanup and dedicated consumer-cancellation plus `aclose()` regression coverage. Security hardening CI for the correction passed.

Reference scan: `docs/REFERENCE_PROJECT_UPDATE_SCAN_2026-09-10.md`.

## Current gate

M5 final regression is current.

The one-shot M5 gate performs the already-proven Stage A-F aggregate check, requires the current release-critical Codex regression set, runs the complete current `tests/test_codex_*.py` family, restarts UWA from the final checkout so M4 and the native remote-compaction lifecycle fix are actually loaded, then performs a fresh same-Codex-thread continuity smoke across another real UWA restart.

The live M5 smoke remains on `uwa / chatgpt / high`, requires real local `exec_command` activity on the resumed turn, verifies the runtime-only continuity token independently, proves post-marker UWA route/completion metadata, requires request-manager cleanup, and does not use the official Codex provider.

Gate: `docs/CODEX_M5_FINAL_REGRESSION_GATE_2026-09-10.md`.

Runner: `tools/codex_m5_final_regression.py`.

## Release-critical sequence

```text
M1 P1.2 same-thread post-remote recovery          PASS / CLOSED
M2 P1.3 minimal continuity blockers               PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                   PASS / LIVE / CLOSED
M3b Desktop UI D1-D5                              PASS / LIVE / CLOSED
M4 real-project long-task pilot                   PASS / LIVE / CLOSED
M5 final A-F + compaction + restart regression    CURRENT
M6 CI + public-repo safety + docs/license         pending
M7 branch topology inspection + merge to main     pending
```

## Main merge rules

Before M7:

- all release-critical CI must be green;
- public-repo safety checks must pass;
- tracked docs and README must reflect current status;
- license/provenance/attribution must remain intact;
- no private browser/session/prompt/tool state may be committed;
- branch topology must be inspected before changing `main`.

The Draft PR stays Draft until these gates are complete.

## Post-main standalone repository

After verified V2 is merged to `main`:

```text
S1 dependency/import/runtime audit + core manifest
S2 create standalone attributed repository
S3 full CI/live parity acceptance
S4 first standalone research release
```

Extraction preserves the genuinely required upstream runtime and AGPL-3.0/copyright attribution while removing unrelated generic UWA surface only when dependency proof says it is safe.

Recent reference-project ideas that do not affect first-release correctness, including structured MCP outputs, durable AgentTask/TaskAttempt/checkpoint orchestration, multi-agent wait semantics, optional Desktop/tunnel packaging and broader file-tool safety fencing, remain deferred until the post-main S1 audit.