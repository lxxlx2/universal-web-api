# P1.2 recovery diagnostic import-path failure — 2026-09-08

## Classification

Operator diagnostic invocation failure. This did not execute a Codex recovery turn and did not call ChatGPT Web.

## Observed result

The read-only timeout diagnostic was invoked from the repository root with a package import of `tools.codex_remote_compaction_recovery`. That module imports `tools.codex_auto_compact_trigger_probe`, whose current import path expects the `tools/` directory itself to be present on `sys.path` for `codex_large_context_acceptance`.

Observed terminal failure:

```text
ModuleNotFoundError: No module named 'codex_large_context_acceptance'
```

## Impact

- No recovery thread was resumed.
- No Web request was issued.
- No compaction or tool continuation state changed.
- Existing private timeout trace remains the source for the next read-only diagnostic.

## Next step

Re-run only the timeout-trace diagnostic with both the repository root and `tools/` on `PYTHONPATH`. Do not run the live recovery gate again until the saved partial trace has been classified.
