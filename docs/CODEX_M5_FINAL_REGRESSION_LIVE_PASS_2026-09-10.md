# M5 final regression live pass — 2026-09-10

## Result

M5 final regression is `PASS / LIVE / CLOSED`.

The accepted run used the guarded one-shot M5 V2 runner on `codex-web-bridge-v2`, configured as `uwa / chatgpt / high`. The repository was clean before and after the run. No official Codex provider quota was used.

## Deterministic regression evidence

```text
private Stage A-F deterministic replay setup        PASS
Stage A-F aggregate                                  PASS
current Codex regression files                       37
required release-critical test files                 present
py_compile                                            PASS
Codex regression tests                               201 passed / 0 failed
git diff --check                                     PASS
repository dirty after tests                         0
```

The historical Stage A-F live workspace was treated as immutable historical evidence. M5 used a fresh private replay fixture under `~/.uwa`, validated it with the current aggregate checker, and removed it after the check.

## Restart-continuity live evidence

```text
first UWA restart                                    PASS
first restart health                                 healthy / browser connected / running=0
seed Codex turn                                      PASS
seed turn tool activity                              zero
seed thread identity                                 captured
runtime token leak before restart                    NO
second UWA restart                                   PASS
second restart health                                healthy / browser connected / running=0
same Codex thread after restart                      YES
resumed turn                                         completed
real local client tool activity                      YES
completed local commands                             2
continuity result exact                              YES
post-marker agent requests/responses                 5 / 5
post-marker latest response status                   completed
authoritative route                                  uwa / chatgpt / high
route expectation failures                           NONE
final request-manager running count                  0
final browser connection                             healthy
private synthetic workspace cleanup                  PASS
repository clean after live run                      YES
```

The live continuation therefore survived a real UWA process restart after process-local Web affinity was removed, while Codex remained the local execution authority and performed real client-side command execution on the resumed turn.

## Release state

```text
M1   PASS / CLOSED
M2   PASS / CLOSED
M3a  PASS / LIVE / CLOSED
M3b  PASS / LIVE / CLOSED
M4   PASS / LIVE / CLOSED
M5   PASS / LIVE / CLOSED
M6   CURRENT
M7   pending
```

M6 now owns the final CI, public-repository safety, documentation, provenance and license review. No new product scope is added in M6.
