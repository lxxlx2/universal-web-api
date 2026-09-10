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
P1.2 stream/usage + TokenCount                       PASS
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

The one-shot hybrid finalizer completed successfully on 2026-09-10.

H3 final evidence:

```text
source official effect count                         1
source UWA effect count                              0
official checker                                     PASS
fresh UWA Codex turn                                 turn.completed
real client tool items                               YES
final official effect count                          1
final UWA effect count                               1
handoff checker                                      PASS
agent exec_command response                          YES
agent completed response                             YES
agent request route                                  chatgpt / high
authoritative latest route                           uwa / chatgpt / high
metadata helper excluded from agent accounting       YES
request-manager after                                0
browser connected after                              YES
H3 final handoff                                     PASS / LIVE
```

H4 evidence:

```text
private transition ledger present                    YES
private file mode                                    YES
source route                                         openai / gpt-6-astra / low
target route                                         uwa / chatgpt / high
workspace/session persisted as hashes only           YES
last event                                           complete
H4 transition ledger                                 PASS
```

H5 rechecked the exact two effects, independent checker, no-duplicate rule and UWA route. Result: PASS.

Canonical live record: `docs/CODEX_HYBRID_M3A_LIVE_PASS_2026-09-10.md`.

## Current gate: M4 real-project long-task pilot

M4 is now current. It should use the actual Codex Web Bridge repository rather than another synthetic workspace. The pilot must be a bounded but non-trivial coding task through a fresh UWA Codex turn and must prove:

```text
preflight route = uwa / chatgpt / high
real local exec_command / file editing = YES
non-trivial implementation diff = YES
regression coverage added = YES
focused validation = PASS
git diff --check = PASS
post-turn request-manager running count = 0
authoritative post-marker route = uwa / chatgpt / high
verified change committed and pushed only after checks pass
```

The selected task is the outstanding V2 stream-cancellation hardening item: when the outer streamed ASGI generator is cancelled or closed before `_run_chat_completion_final` completes, its backing task must be cancelled and awaited so no browser/request work survives as an orphan. Caller cancellation must still propagate, and normal completion behavior must remain unchanged.

One-shot runner: `tools/codex_m4_real_project_pilot.py`.

## Accelerated release-critical path

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       PASS / LIVE / CLOSED
M3b Desktop UI D1-D5                                  PASS / LIVE / CLOSED
M4 one real-project long-task pilot                   CURRENT
M5 final A-F + compaction + restart regression        pending
M6 CI green + public-repo safety + docs/provenance    pending
M7 branch-topology inspection + merge to main         pending
```

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

- `docs/CODEX_HYBRID_M3A_LIVE_PASS_2026-09-10.md`
- `docs/CODEX_H3_REQUIRED_TOOL_REPAIR_LIVE_PASS_2026-09-10.md`
- `docs/CODEX_H3_METADATA_HELPER_ISOLATION_LIVE_PASS_2026-09-10.md`
- `docs/CODEX_H3_FINAL_HANDOFF_LIVE_GATE_2026-09-10.md`
- `docs/CODEX_DESKTOP_D5_LIVE_PASS_2026-09-09.md`
- `docs/ACCELERATED_MAIN_MERGE_GATE_2026-09-08.md`

## Recording discipline

Every live result, failure, repair and disruptive checkpoint is committed before the next step. README, canonical current state, this file and Draft PR #2 should stay aligned. Public records contain only non-sensitive evidence and omit private prompt/tool bodies, raw account/thread/process/browser identifiers and private trace contents.
