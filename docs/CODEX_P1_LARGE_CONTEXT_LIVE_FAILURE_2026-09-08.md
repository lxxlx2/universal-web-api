# P1.2 large-context first live failure — 2026-09-08

## Status

LIVE BLOCKED / DIAGNOSIS CURRENT.

The first real macOS run of `tools/codex_large_context_acceptance.py run` did not reach the final recovery checker.

Observed public-safe terminal evidence:

```text
CONTEXT_WINDOW=64000
FILLER_BYTES_PER_ROUND=20000
MAX_ROUNDS=24
SEED_REPLY_EXACT=YES
SEED_TOOL_EFFECTS=0
ROUND=01 ACK_EXACT=YES TOOL_EFFECTS=0 INPUT_TOKENS=0 COMPACT_ROUTE_DELTA=0 COMPACT_SUCCESS_DELTA=0
ROUND=02 ACK_EXACT=YES TOOL_EFFECTS=0 INPUT_TOKENS=0 COMPACT_ROUTE_DELTA=0 COMPACT_SUCCESS_DELTA=0
ROUND=03 ACK_EXACT=YES TOOL_EFFECTS=0 INPUT_TOKENS=0 COMPACT_ROUTE_DELTA=0 COMPACT_SUCCESS_DELTA=0
ROUND=04 ACK_EXACT=YES TOOL_EFFECTS=0 INPUT_TOKENS=0 COMPACT_ROUTE_DELTA=0 COMPACT_SUCCESS_DELTA=0
ROUND=05 ACK_EXACT=YES TOOL_EFFECTS=0 INPUT_TOKENS=0 COMPACT_ROUTE_DELTA=0 COMPACT_SUCCESS_DELTA=0
ROUND=06 ACK_EXACT=YES TOOL_EFFECTS=0 INPUT_TOKENS=0 COMPACT_ROUTE_DELTA=0 COMPACT_SUCCESS_DELTA=0
ROUND=07 ACK_EXACT=YES TOOL_EFFECTS=0 INPUT_TOKENS=0 COMPACT_ROUTE_DELTA=0 COMPACT_SUCCESS_DELTA=0
RUN_FAIL round=8 Codex turn failed rc=1
```

The private trace remains only under `~/.uwa/p1-large-context/` and is not committed.

## What is proven

- The seed contract passed.
- Seven same-run filler turns returned their exact ACKs with zero observed tool effects.
- The eighth Codex continuation failed with a non-zero client exit status.
- P1.2 live is not PASS and no compaction claim is made.

## Instrumentation gaps discovered

Two observations from this output are not yet safe to interpret as protocol conclusions.

### Failure-turn compact evidence is currently dropped

`_run_codex_turn()` raises immediately on a non-zero Codex exit status. The outer filler loop returns on that exception before `scan_log_delta()` runs for the failed turn.

Therefore the printed `COMPACT_ROUTE_DELTA=0` / `COMPACT_SUCCESS_DELTA=0` values only cover successful rounds 1-7. They do **not** prove that round 8 failed before `/v1/responses/compact` was attempted. Round 8 may have generated compact lifecycle evidence that the current runner failed to harvest.

### `INPUT_TOKENS=0` is not yet classified

Every successful filler round printed zero input tokens. This can mean either:

1. the current Codex JSONL/provider path reports zero/missing usage for these UWA responses; or
2. the runner's usage extraction assumption does not match the actual live JSONL shape.

Until the private trace is inspected through a bounded redacted diagnostic, zero usage is treated as an instrumentation signal, not evidence that conversation context did not grow.

## Current diagnostic gate

Do not rerun the 24-round acceptance yet and do not change compact protocol code yet.

Next evidence must be extracted without publishing raw private traces:

1. event-type and failure-message summary from only `turn-08-filler.jsonl`, with thread/item ids and prompt/message bodies suppressed;
2. actual `turn.completed` usage shape from one successful filler trace;
3. bounded UWA log lines around the run containing only compact/error lifecycle keywords.

After this diagnostic, decide whether the blocker is compact runtime behavior, Codex context handling, or acceptance-runner instrumentation.
