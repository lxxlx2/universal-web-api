# Post-main standalone repository plan — 2026-09-08

## Decision

Create a clearer standalone repository **after the accelerated release-critical gates pass and the verified V2 is merged into `main`**.

This is not a clean-room rewrite and does not need to be one. The goal is a smaller, clearer, easier-to-use open-source research repository that preserves the real provenance of reused code while separating the Codex Web Bridge core from unrelated upstream surface area.

## Current provenance

The current repository is a GitHub fork of:

```text
lumingya/universal-web-api
```

and carries the upstream AGPL-3.0 license and Git history.

The current `codex-web-bridge-v2` branch also contains substantial independently implemented Codex bridge work, including Codex Responses adapters, web-session affinity, tool-policy enforcement, stream compatibility, remote compaction V2, provider switching, acceptance tooling and project-specific hardening.

Therefore the future standalone repository must state clearly:

- which upstream project supplied the original browser/API foundation;
- which code remains derived from/reused from that foundation;
- which additional projects were design references only;
- which bridge components were newly implemented in this project;
- the applicable license and attribution obligations.

Rewriting working upstream-derived foundations solely to remove provenance is unnecessary.

## Why wait until after main

Do not perform repository extraction during the remaining release gates.

Reasons:

1. the existing fork is the verified integration environment;
2. current tests, browser automation, lifecycle helpers and acceptance evidence already target this tree;
3. deleting or relocating upstream modules now would create unrelated regression risk;
4. a known-good `main` commit gives extraction a stable source snapshot;
5. the standalone repository can then be validated against the exact same acceptance matrix.

## Accelerated prerequisite

The standalone extraction does **not** wait for broad P2-P5 feature expansion. It begins after the release-critical main gate defined in `docs/ACCELERATED_MAIN_MERGE_GATE_2026-09-08.md`:

```text
P1.2 same-thread post-remote recovery
P1.3 minimal continuity blockers
Desktop UI D1-D5 + Medium/High verification
one real-project long-task pilot
final regression / CI / public-repo safety / docs
branch-topology inspection
merge verified V2 to main
```

Broad P2-P5 hardening may continue after `main` and can be incorporated into the standalone repository incrementally.

## What likely belongs in the standalone core

The exact list will be produced from an import/runtime dependency audit, not by filename guessing. Expected core categories are:

```text
Codex Responses / tool protocol adapters
ChatGPT Web browser-mode control
browser/session continuity needed by the bridge
client tool policy and safety boundary
stream / usage / compaction compatibility
provider/lifecycle/memory helpers
public-repo safety checks
acceptance and regression tests
minimal runtime/config/logging dependencies
README / architecture / security / attribution docs
```

## Candidate upstream surface for exclusion

The current fork still contains broad generic UWA functionality that may not be required by the Codex bridge. Examples include generic provider/API surfaces, unrelated protocol adapters, generic configuration/UI routes, assets and legacy operational features.

These are **candidates only**. None should be removed from the current development repository based solely on naming. Before exclusion, the extraction must prove they are absent from the bridge's import graph and runtime/acceptance path.

## Extraction method

Preferred approach after `main` merge:

1. tag or record the exact source `main` commit used for extraction;
2. generate an import/runtime dependency inventory from the verified Codex bridge entry points;
3. classify files as `core`, `required-upstream-runtime`, `optional`, or `unrelated`;
4. create the new standalone repository from the curated tree;
5. preserve AGPL-3.0 where upstream-derived AGPL code remains;
6. include explicit `UPSTREAM.md` / attribution naming `lumingya/universal-web-api` and other references;
7. retain copyright/license notices required by reused files;
8. make the new README start with install/use/provider-mode instructions rather than fork history;
9. run the complete bridge regression and live acceptance suite against the new repository;
10. only call the standalone repository stable after its results match the known-good source commit.

A history-preserving filtered extraction is preferred when practical because it retains authorship/provenance naturally. A curated source snapshot is also possible if all required license/copyright/attribution notices are preserved.

## Proposed user-facing repository shape

```text
README.md
LICENSE
UPSTREAM.md
SECURITY.md
app/
  bridge/
  browser/
  runtime/
tools/
tests/
docs/
```

Exact package names are deferred until the dependency audit so imports are not churned before the current release is stable.

## Validation gate for the new repository

The standalone extraction is not complete until it passes:

```text
unit/regression CI                         PASS
public-repo safety                         PASS
UWA provider switch / official restore     PASS
Codex CLI tool loop                         PASS
large-context / compaction                  PASS
restart / lost-affinity recovery            PASS
Desktop D1-D5                               PASS
real-project pilot                          PASS
```

The old fork should remain available as development/provenance history at least through the first stable standalone release.

## Timing

```text
NOW
  accelerated release-critical gate

THEN
  merge verified V2 to main

POST-MAIN S1
  dependency/import/runtime audit + core manifest

POST-MAIN S2
  create standalone repository with license/attribution

POST-MAIN S3
  run full CI/live parity acceptance

POST-MAIN S4
  publish first standalone research release
```
