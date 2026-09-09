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
P1.2 native auto-compact                           PASS
P1.2 remote V2 compaction                          PASS / LIVE
P1.2 same-thread post-remote recovery              PASS / CLOSED
P1.3 minimal continuity blockers                   PASS / CLOSED
Hybrid H0-H2                                       PASS
Desktop D1-D5                                      PASS / LIVE / CLOSED
ChatGPT idle-composer send repair                  PASS / LIVE
```

## Current gate

Hybrid H3 is current.

The official source half is already accepted and must not be rerun unnecessarily. The UWA continuation half remains open.

Two H3-specific issues remain:

```text
client-tool exposure / required-tool path
metadata_helper vs agent_turn isolation
```

The earlier browser-send stall is closed. Commit `1dac853` repaired the ChatGPT idle-composer false positive, and the direct High live rerun now reaches the terminal Responses completion path with clean browser/request cleanup.

A tiny post-fix Codex CLI probe also reaches `turn.completed` without the former stream disconnect, but the controlled web turn reports that `exec_command` is unavailable. Metadata-only wire evidence must now identify whether the tool was missing from the Codex request, lost inside UWA tool exposure, or present with required-tool detection missed.

## Release-critical sequence

```text
M1 P1.2 same-thread post-remote recovery          PASS / CLOSED
M2 P1.3 minimal continuity blockers               PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                   CURRENT
     H0                                           PASS
     H1                                           PASS
     H2                                           PASS / LIVE / CLOSED
     H3                                           CURRENT
     H4                                           marker foundation present
     H5                                           pending
M3b Desktop UI D1-D5                              PASS / LIVE / CLOSED
M4 real-project long-task pilot                   pending
M5 final A-F + compaction + restart regression    pending
M6 CI + public-repo safety + docs/license         pending
M7 branch topology inspection + merge to main     pending
```

## H3 closure requirements

The preserved synthetic handoff workspace must prove:

```text
official source effect count = 1
UWA continuation effect count = 1
real required client tool call = YES
metadata helper excluded from agent accounting = YES
agent route = uwa / chatgpt / high
```

No result from a hidden title/description helper can satisfy the agent-turn requirement.

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
