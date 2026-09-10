# M7 topology and main merge gate — 2026-09-10

## Purpose

M7 is the final gate for the first verified Codex Web Bridge V2 integration. It changes no product behavior. It verifies branch ancestry and final-head CI, then advances `main` to the exact tested release tree without rewriting release history.

## Verified release baseline

```text
M1   PASS / CLOSED
M2   PASS / CLOSED
M3a  PASS / LIVE / CLOSED
M3b  PASS / LIVE / CLOSED
M4   PASS / LIVE / CLOSED
M5   PASS / LIVE / CLOSED
M6   PASS / CLOSED
M7   CURRENT
```

M5 live evidence is recorded in `docs/CODEX_M5_FINAL_REGRESSION_LIVE_PASS_2026-09-10.md`. M6 release-safety evidence is recorded in `docs/CODEX_M6_RELEASE_SAFETY_AUDIT_2026-09-10.md`.

## Topology inspection

GitHub compare data immediately before this gate showed:

```text
main -> codex-web-bridge-v2
status                 ahead
behind_by              0
merge base             exact current main head

security-hardening -> codex-web-bridge-v2
status                 ahead
behind_by              0
merge base             exact security-hardening head
```

Therefore both `main` and the verified `security-hardening` base are ancestors of the release branch. No side-branch reconciliation, force push or history rewrite is required.

The repository's `main` branch is currently reported by GitHub as unprotected, so this project applies its own fail-closed merge gate instead of relying on branch protection.

## Pull-request topology

Draft PR #2 was created during V2 development with `security-hardening` as its base. That base was useful while the release branch was being validated, but the actual release destination is `main`.

For M7, PR #2 may be retargeted to `main` for final release visibility. The release operation itself should preserve the exact tested branch history/tree. Because `main` is an ancestor of the release branch, a non-forced fast-forward of `main` to the final green release head is the preferred topology. This avoids rebasing or squashing hundreds of validated commits into new untested commit identities.

## Final-head CI requirement

The M6 documentation/status head passed Security hardening before this M7 gate was created. This M7 gate document is the final planned pre-merge branch commit.

Before advancing `main`, GitHub Actions for the exact commit containing this document must complete successfully. Required release-relevant jobs remain:

```text
public-repo-safety
security-tests Ubuntu 3.11
security-tests Ubuntu 3.13
security-tests macOS 3.11
security-tests macOS 3.13
upstream-regression
```

A pending, cancelled or failed exact-head workflow blocks the merge.

## Merge contract

M7 may close only when all of these are true:

```text
M5 final live regression                         PASS / LIVE / CLOSED
M6 release-safety review                         PASS / CLOSED
final branch head CI                             PASS
main behind release branch                       YES
release branch behind main                       NO
security-hardening ancestor                      YES
force update required                            NO
main advanced to exact final release head        YES
post-update main tree equals release tree        YES
```

The main ref update must use fast-forward semantics only. `force=true` is forbidden.

## Post-merge

After `main` contains the verified V2 release tree, release-critical M1-M7 work is complete. The next phase is the already-defined standalone plan:

```text
S1 dependency/import/runtime audit + core manifest
S2 standalone attributed repository
S3 full CI + CLI/Desktop/live parity acceptance
S4 first standalone research release
```

The standalone extraction remains subject to AGPL-3.0, copyright notices and explicit upstream attribution. Nonblocking ideas from the 2026-09-10 reference-project scan remain deferred to that phase.
