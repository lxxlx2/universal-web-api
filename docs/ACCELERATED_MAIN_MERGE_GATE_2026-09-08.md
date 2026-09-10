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
```

## M3a closed

The final synthetic official -> UWA handoff acceptance passed. The official source effect remained exactly once, the UWA continuation effect occurred exactly once, the independent handoff checker passed, a real `exec_command` client tool call occurred, metadata-helper traffic was excluded from agent accounting, authoritative route metadata resolved to `uwa / chatgpt / high`, the private transition ledger passed, and request-manager returned to zero.

Detailed record: `docs/CODEX_HYBRID_M3A_LIVE_PASS_2026-09-10.md`.

## Current gate

M4 real-project long-task pilot is current.

The pilot uses this repository itself and closes a known V2 runtime lifecycle item: the backing `_run_chat_completion_final` task created by the streamed Responses attempt must be cancelled and awaited when the outer async/ASGI stream is cancelled or closed early. Caller cancellation must still propagate and normal completion behavior must remain unchanged.

M4 requires one fresh verified `uwa / chatgpt / high` Codex coding turn, real local client tool activity, a bounded implementation diff plus regression coverage, independent focused validation, clean post-turn request-manager state, and guarded commit/push only after all checks pass.

Gate: `docs/CODEX_M4_REAL_PROJECT_LONG_TASK_GATE_2026-09-10.md`.

## Release-critical sequence

```text
M1 P1.2 same-thread post-remote recovery          PASS / CLOSED
M2 P1.3 minimal continuity blockers               PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                   PASS / LIVE / CLOSED
M3b Desktop UI D1-D5                              PASS / LIVE / CLOSED
M4 real-project long-task pilot                   CURRENT
M5 final A-F + compaction + restart regression    pending
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
