# M5 local validation bootstrap recovery — 2026-09-10

## Observed live result

The first M5 final-regression attempt failed before Stage A-F or the Codex regression suite ran.

Safe observed metadata:

```text
branch                                  codex-web-bridge-v2
worktree                                clean
M4 implementation present               YES
remote-compaction fix present            YES
configured route                         uwa / chatgpt / high
Codex CLI present                        YES
Stage A-F workspace guarded              YES
validation Python candidates tested      5
validation Python ready                  NO
failure class                            no_repo_capable_python
```

## Classification

This is a local validation-environment blocker in the M5 harness, not a product regression.

The production `requirements.txt` intentionally contains runtime dependencies and does not include `pytest`. The first M5 runner incorrectly required each candidate interpreter to import `fastapi`, the Codex project modules and `pytest` in one probe. A runtime-capable Python can therefore be rejected solely because it lacks the development-only test runner.

M4 had already demonstrated a local Python capable of importing the project runtime without requiring pytest in the same probe.

## Recovery

`tools/codex_m5_final_regression_safe.py` separates the two concerns:

```text
1. select a Python that can import the UWA/Codex runtime
2. reuse that interpreter directly when pytest is already available
3. otherwise install pytest only into private ~/.uwa validation state
4. expose that private pytest target through a small local launcher
5. run the unchanged M5 final-regression logic with that validation interpreter
```

The bootstrap does not modify tracked repository files or production requirements. It does not switch providers and does not use the official Codex provider.

The private dependency location is local validation state only and must never be committed.

## Release impact

M5 remains `CURRENT`. No M5 correctness assertion has failed yet because the first run stopped before the deterministic regression block.

Release-critical state remains:

```text
M1   PASS / CLOSED
M2   PASS / CLOSED
M3a  PASS / LIVE / CLOSED
M3b  PASS / LIVE / CLOSED
M4   PASS / LIVE / CLOSED
M5   CURRENT / local validation bootstrap repaired
M6   pending
M7   pending
```

Security hardening CI for the safe bootstrap commit completed successfully before the next local rerun was authorized.
