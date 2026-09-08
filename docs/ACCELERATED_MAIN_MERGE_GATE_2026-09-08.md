# Accelerated main-merge gate — 2026-09-08

## Decision

The project is moving from broad hardening exploration to a release-focused sequence.

The existence of multiple adjacent ChatGPT/Codex bridge projects is not a reason to pivot architecture or chase feature parity. The current bridge already has a verified local-tool loop, restart continuity, large-context accounting, native auto-compaction, real remote V2 compaction, same-thread post-compaction token recovery and the minimal P1.3 continuity fences. The fastest path to a useful public research release is to finish only the remaining user-facing/blocking gates before `main`, then continue non-blocking hardening after `main` and during the standalone-repository phase.

A pre-D1 Desktop event added one narrow release-critical requirement: routing must be visible and auditable. An existing Desktop conversation resumed as official `openai / gpt-6-astra / ultra` and consumed official allowance while separate UWA-backed sessions also existed. Therefore provider config alone is not sufficient user-facing evidence. The project now includes a minimal Hybrid Routing Safety block inside M3; this does not change the accelerated release strategy.

Detailed routing plan: `docs/CODEX_HYBRID_ROUTING_SAFETY_2026-09-08.md`.

## What remains merge-blocking

```text
M1 P1.2 same-thread post-remote-compaction recovery       PASS / CLOSED
M2 P1.3 minimal continuity blockers                        PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                            CURRENT
   - metadata-only route identity / audit helper
   - explicit route intent + no-silent-downgrade guard
   - tiny fresh-thread Desktop route probe
   - explicit official -> UWA handoff on current workspace state
   - private transition ledger
M3b Desktop UI D1-D5                                       CURRENT after route probe
   - real Desktop local tool round trip
   - same Desktop thread continuation
   - full Desktop restart/history resume
   - Desktop + UWA restart recovery
   - clean official-account restore
   - Medium/High reasoning end-to-end verification folded into this gate
M4 one real-project long-task pilot
M5 final A-F + compaction + restart regression
M6 CI green + public-repo safety + documentation/provenance/license checks
M7 inspect branch topology, then merge verified V2 to main
```

## P1.2 closure

P1.2 is closed on composite live + CI evidence:

```text
native remote V2 compaction                         PASS
same private Codex thread resume                    PASS
conversation-only token recovery                    PASS
real local write                                    PASS
exact result                                        PASS
private history search                              NO
body_after_prefix anti-thrash migration             PASS
compaction growth during decisive recovery          NO
staged deterministic recovery harness CI #473       PASS
```

Detailed closure: `docs/CODEX_P1_REMOTE_V2_RECOVERY_CLOSED_2026-09-08.md`.

## P1.3 closure

The accelerated minimal continuity block is also closed:

```text
lost-affinity / restart fallback                    PASS
stable response/conversation identity               PASS
conflicting call-id stale fencing                   PASS
no retry after real client function_call            PASS
no retry after response.failed                      PASS
bounded repair only before client tool effect       PASS
Security hardening CI #478 / #483 / #486            PASS
```

This closes the three correctness risks that could otherwise lose, duplicate or mis-associate work across restart and retry boundaries.

Detailed closure: `docs/CODEX_P1_3_MINIMAL_CONTINUITY_CLOSED_2026-09-08.md`.

## Active gate: Hybrid Routing Safety + Desktop UI

M3 remains the release-critical gate. CLI/protocol evidence cannot substitute for actual ChatGPT Desktop Codex behavior, and config state alone cannot substitute for per-session route evidence.

Required Hybrid Routing Safety behavior before long Desktop work:

```text
route/provider/model/effort visible before long task     REQUIRED
wrong-route fresh probe                                  STOP / fail closed
premium official route                                   never spent silently
UWA fallback/handoff                                     explicit and auditable
quality floor                                            never silently downgraded
unknown quota state                                      never guessed
```

The intended hybrid operating mode is:

```text
explicit official route + acceptable model/effort
→ use official allowance knowingly

official quota exhausted/unavailable or explicit switch
→ preserve local workspace/Git state
→ switch to UWA
→ verify fresh UWA route
→ continue in a fresh UWA thread using a local-only handoff checkpoint
```

Do not claim transparent in-place migration of an existing Desktop thread until proven. Existing Desktop threads may retain provider/model identity.

After H0-H2 are in place, Desktop scenarios continue sequentially:

```text
D1 native Desktop tool round trip
D2 same Desktop thread continuation
D3 Desktop application restart/history resume
D4 Desktop + UWA process restart recovery
D5 clean restore to normal official-account mode
```

Medium/High request-to-page verification is folded into this gate so that UI controls are only considered supported after the actual Desktop request reaches UWA and the ChatGPT Web page state is verified.

## What no longer blocks the first main merge

The following remain valuable but are moved to post-main hardening unless a blocker discovered by M3-M6 requires them earlier:

```text
P2 broad per-continuation concurrency architecture
P2 generalized browser lease/governance framework
P3 broad MCP/schema/capability normalization
P4 expanded evidence/trust-order framework
P5 full doctor/preflight productization
fully automatic unsupported/private quota polling
background automatic thread migration
provider cost optimization / generalized routing engine
rich routing dashboard
automatic model benchmarking/task classifier
optional first-party page-runtime submission research
broad removal of generic upstream UWA surface
```

These items should continue after the first verified `main` baseline and can be incorporated into the standalone repository when they improve maintainability without destabilizing the core bridge.

## Why this is safe

Already live/CI verified:

```text
Stage A-F protocol/CLI acceptance                    PASS
aggregate A-F checker                                PASS
real local tool execution                            PASS
same-thread/restart continuity                       PASS
P1.1 legacy compact                                  PASS
stream heartbeat + non-zero usage                    PASS
TokenCount persistence                               PASS
native threshold/local fallback                      PASS
remote capability shim implementation/CI             PASS
remote V2 protocol implementation/CI                 PASS
managed UWA precondition                             PASS
native remote V2 compaction macOS live               PASS
same-thread post-remote token continuity             PASS
body-after-prefix anti-thrash behavior               PASS
minimal P1.3 continuity correctness                  PASS
local metadata can distinguish openai/astra/ultra
from uwa/chatgpt/high                                 PASS
```

The remaining merge blockers therefore test user-facing route safety, Desktop integration, one real-project workload and final release regression/safety rather than foundational protocol discovery.

## Expected remaining effort

If no new blocker appears:

```text
1 focused Hybrid Routing Safety block H0-H5
5 Desktop scenarios D1-D5 (reasoning verification folded in)
1 real-project pilot
1 final regression/safety/docs pass
1 topology/merge step
```

This is still the release-critical path. Do not add adjacent-project features or broad routing automation unless they fix an observed failure in these gates.

## After main

Immediately after a verified merge to `main`:

```text
S1 dependency/import/runtime audit
S2 create clearer standalone attributed repository
S3 parity CI/live acceptance
S4 first standalone research release
```

P2-P5 hardening and richer hybrid routing automation can continue against the stable `main` baseline and/or the standalone repository without delaying the first usable public release.
