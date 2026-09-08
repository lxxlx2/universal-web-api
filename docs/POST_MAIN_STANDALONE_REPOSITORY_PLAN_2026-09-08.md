# Post-main standalone repository plan — 2026-09-08

## Decision

Create a clearer standalone repository **after the current V2 work has passed all mandatory gates and has been merged into `main`**.

This is not a clean-room rewrite and does not need to be one. The goal is a smaller, clearer, easier-to-use open-source research repository that preserves the real provenance of reused code while separating the Codex Web Bridge core from unrelated upstream surface area.

## Current provenance

The current repository is a GitHub fork of:

```text
lumingya/universal-web-api
```

and carries the upstream AGPL-3.0 license and Git history.

The current `codex-web-bridge-v2` branch also contains substantial independently implemented Codex bridge work, including Codex Responses adapters, web-session affinity, tool-policy enforcement, stream compatibility, remote compaction V2, provider switching, acceptance tooling and project-specific hardening.

Therefore the future standalone repository must **not** claim that every line was independently created or that the project only borrowed ideas. It should state clearly:

- which upstream project supplied the original browser/API foundation;
- which code remains derived from/reused from that foundation;
- which additional projects were design references only;
- which bridge components were newly implemented in this project;
- the applicable license and attribution obligations.

That transparency is sufficient for the intended open-source research use; rewriting working upstream-derived foundations solely to remove provenance is unnecessary.

## Why wait until after merge to main

Do not perform repository extraction during the current P1/P2 hardening work.

Reasons:

1. the existing fork is the verified integration environment;
2. current tests, browser automation, lifecycle helpers and acceptance evidence already target this tree;
3. deleting or relocating upstream modules now would create unrelated regression risk;
4. a known-good `main` commit gives the extraction a stable source snapshot;
5. the standalone repository can then be validated against the exact same acceptance matrix.

The extraction starts only after the existing final merge gate has passed and V2 is merged to `main`.

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
6. include an explicit `UPSTREAM.md` / attribution document naming `lumingya/universal-web-api` and other references;
7. retain copyright/license notices required by reused files;
8. make the new README start with install/use/provider-mode instructions rather than fork history;
9. run the complete bridge regression and live acceptance suite against the new repository;
10. only call the standalone repository stable after its results match the known-good source commit.

A history-preserving filtered extraction is preferred when practical because it retains authorship/provenance naturally. A curated source snapshot is also possible if all required license/copyright/attribution notices are preserved. The choice is a repository-maintenance decision, not a reason to rewrite working code.

## Proposed user-facing repository shape

The new repository should optimize for a new user rather than for upstream parity. A likely top-level shape is:

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
  current P1.2/P1.3/P2-P5 and Desktop/release gates

THEN
  merge verified V2 to main

POST-MAIN PHASE S1
  dependency/import audit + core manifest

POST-MAIN PHASE S2
  create standalone repository with license/attribution

POST-MAIN PHASE S3
  run full CI/live parity acceptance

POST-MAIN PHASE S4
  publish first standalone research release
```

This keeps the current core work moving and postpones repository cleanup until it can no longer destabilize the release candidate.
