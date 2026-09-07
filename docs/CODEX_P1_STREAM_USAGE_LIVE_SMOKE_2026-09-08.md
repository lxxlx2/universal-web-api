# P1.2 stream/usage live smoke — 2026-09-08

## Status

PASS.

This smoke followed the first P1.2 large-context failure and the stream-compatibility repair in `app/services/codex_stream_compat.py`.

## Purpose

Before repeating the expensive full large-context run, prove on the real macOS runtime that:

1. UWA actually restarted onto the repaired server code;
2. the Codex Responses stream still completes normally;
3. Codex receives non-zero token usage so native auto-compaction can accumulate toward its threshold.

## Live evidence

```text
LISTENER_REPLACED=YES
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
CODEX_RC=0
REPLY_EXACT=YES
INPUT_TOKENS=7113
OUTPUT_TOKENS=54
NONZERO_USAGE=YES
ERROR_COUNT=0
USAGE_SMOKE_PASS=YES
CODEX_USAGE_MARKERS=1
P1_STREAM_USAGE_SMOKE_PASS
```

The UWA log delta contained one numeric-only compatibility marker confirming the conservative local usage estimator supplied `input_tokens=7113` and `output_tokens=54` for this turn.

## Interpretation

The previous blocker where Codex observed `input_tokens=0` on every completed turn is closed for the real runtime. Native Codex session usage can now grow, so its own auto-compact threshold logic can become reachable.

The listener was also replaced before the smoke, preventing stale bytecode from being mistaken for the repaired implementation.

This smoke does not itself prove compaction. P1.2 remains open until the full same-thread large-context run produces explicit successful `/v1/responses/compact` evidence and then recovers the conversation-only token through the final exact local-tool checker.

## Next gate

Run the full P1.2 live entry via `tools/codex_large_context_live.py run`. The live wrapper preserves failed-turn UWA log evidence if a future Codex turn exits non-zero.

## Safety

Raw Codex JSONL and UWA logs remain private under `~/.uwa`. This public record contains only bounded counters, booleans and synthetic acceptance metadata.
