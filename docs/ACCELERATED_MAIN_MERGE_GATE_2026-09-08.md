# Accelerated main-merge gate — 2026-09-08

## Decision

The project is moving from broad hardening exploration to a release-focused sequence.

The existence of multiple adjacent ChatGPT/Codex bridge projects is not a reason to pivot architecture or chase feature parity. The current bridge already has a verified local-tool loop, restart continuity, large-context accounting, native auto-compaction and real remote V2 compaction. The fastest path to a useful public research release is to finish only the remaining correctness/blocking gates before `main`, then continue non-blocking hardening after `main` and during the standalone-repository phase.

## What remains merge-blocking

```text
M1 P1.2 same-thread post-remote-compaction recovery
M2 P1.3 minimal continuity blockers
   - lost-affinity/restart fallback correctness
   - stable identity / stale-generation fencing
   - uncertain tool-effect reconciliation before retry
M3 Desktop UI D1-D5
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

## What no longer blocks the first main merge

The following remain valuable but are moved to post-main hardening unless a blocker discovered by M1-M6 requires them earlier:

```text
P2 broad per-continuation concurrency architecture
P2 generalized browser lease/governance framework
P3 broad MCP/schema/capability normalization
P4 expanded evidence/trust-order framework
P5 full doctor/preflight productization
optional first-party page-runtime submission research
broad removal of generic upstream UWA surface
```

These items should continue after the first verified `main` baseline and can be incorporated into the standalone repository when they improve maintainability without destabilizing the core bridge.

## Why this is safe

Already live-verified:

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
```

The remaining merge blockers therefore test end-to-end recovery and user-facing integration rather than foundational protocol discovery.

## Expected remaining effort

If no new blocker appears:

```text
1 gate   P1.2 post-remote recovery
1 focused implementation/test block   minimal P1.3
5 Desktop scenarios                    D1-D5 (reasoning verification folded in)
1 real-project pilot
1 final regression/safety/docs pass
1 topology/merge step
```

This is the release-critical path. Do not add adjacent-project features to it unless they fix an observed failure in these gates.

## After main

Immediately after a verified merge to `main`:

```text
S1 dependency/import/runtime audit
S2 create clearer standalone attributed repository
S3 parity CI/live acceptance
S4 first standalone research release
```

P2-P5 hardening can continue against the stable `main` baseline and/or the standalone repository without delaying the first usable public release.
