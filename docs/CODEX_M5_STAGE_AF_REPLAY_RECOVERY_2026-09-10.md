# M5 Stage A-F replay recovery — 2026-09-10

## Observed live failure

The second M5 live attempt successfully resolved a repository-capable validation Python and privately bootstrapped pytest, then stopped at the Stage A-F aggregate checker before the current Codex regression family or restart-continuity live smoke ran.

Safe observed summary:

```text
validation runtime                    PASS
private pytest bootstrap              PASS
Stage A-F aggregate RC                1
multi_file                            PASS
failure_recovery                      FAIL
git_diff                              FAIL
interactive                           FAIL
context                               PASS
```

## Classification

This is an acceptance-workspace lifecycle issue, not evidence of a current product regression.

`~/uwa-codex-acceptance` is a mutable live-acceptance workspace. The Desktop acceptance harness deliberately supports `prepare --scenario ...`, which rebuilds an individual scenario in place for later live runs. Therefore the workspace cannot serve as an immutable release artifact after subsequent Desktop/recovery work has reused it.

The original Stage A-F live acceptance and aggregate checker are already closed historical evidence. M5 should revalidate the current acceptance checker deterministically without mutating, deleting or depending on the old mutable workspace.

## Recovery

`tools/codex_m5_final_regression_safe_v2.py` keeps the private pytest bootstrap from the first safe wrapper and replaces only the Stage A-F aggregate source:

```text
historical live Stage A-F status        preserved as PASS / CLOSED
historical workspace                    never modified or deleted
fresh replay workspace                  private under ~/.uwa
replay fixture                          newly initialized from current acceptance harness
completed scenario state                materialized deterministically
aggregate checker                       rerun against fresh private fixture
replay workspace                        removed after the check
```

The replay validates the current checker and scenario invariants. It is not presented as a new live Stage A-F tool-routing run. Live routing/tool continuity remains independently covered later in M5 by the fresh same-Codex-thread restart smoke on `uwa / chatgpt / high` with real local `exec_command` activity.

## Repository safety

The safe v2 runner does not alter production requirements, tracked project files or the historical acceptance workspace. Temporary replay state is created only under private `~/.uwa` state and is guarded before cleanup.

## Release decision

M5 remains CURRENT. No M6 work is unblocked until the safe v2 runner reaches `M5_FINAL_REGRESSION=PASS_LIVE_CLOSED`.
