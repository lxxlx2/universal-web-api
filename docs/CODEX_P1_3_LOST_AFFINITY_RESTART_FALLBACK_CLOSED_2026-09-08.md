# P1.3 lost-affinity / restart fallback — CLOSED — 2026-09-08

This merge-critical P1.3 sub-gate is closed on existing live evidence plus focused regression coverage.

## Live evidence

Stage F previously crossed a real UWA process restart boundary:

- process-local ChatGPT web affinity existed before restart;
- the affinity map was empty after restart;
- the same Codex thread resumed;
- conversation-only context survived without being repeated in the resume prompt;
- real local client-tool execution resumed;
- the independent acceptance checker passed.

That live run already proved that correctness does not depend on the process-local ChatGPT `/c/...` binding surviving.

## Focused restart-fallback regression

`tests/test_codex_lost_affinity_restart_fallback.py` now locks the implementation contract:

1. when in-memory web affinity is absent and process-local Responses state is gone, but private persisted `previous_response_id` history exists, `_prepare_codex_web_turn()` hydrates the persisted history, clears the server history handle, and uses the fresh-chat/full-history fallback rather than the browser delta path;
2. when affinity and persisted state are both absent and the client supplies only an orphan `function_call_output`, the bridge fails closed with 404 instead of inventing missing tool-call history.

This preserves the intended hierarchy:

```text
healthy web affinity -> same ChatGPT conversation + delta
lost/unhealthy affinity + persisted continuation -> fresh chat + reconstructed full history
no trustworthy continuation source -> fail closed
```

## CI

Security hardening workflow run #478 completed successfully across public-repo safety, Ubuntu/macOS Python 3.11/3.13 security jobs, and the reproducible upstream regression suite.

## Gate decision

P1.3 sub-gate `lost-affinity / UWA-restart fallback correctness` is **PASS / CLOSED**.

Next merge-critical sub-gate: stable continuation identity / stale-generation fencing.

No private response contents, SQLite contents, thread ids, browser conversation ids, process ids, or local paths are recorded here.
