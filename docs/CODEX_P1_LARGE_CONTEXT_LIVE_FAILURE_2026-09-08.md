# P1.2 large-context first live failure — 2026-09-08

## Status

LIVE BLOCKED / SSE IDLE-TIMEOUT DIAGNOSIS CURRENT.

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

## Redacted diagnosis

A bounded diagnostic of one successful trace and the failed round produced:

```text
turn-07-filler.jsonl:
  thread.started=1
  turn.started=1
  item.completed:agent_message=1
  turn.completed=1
  usage={
    input_tokens: 0,
    cached_input_tokens: 0,
    cache_write_input_tokens: 0,
    output_tokens: 0,
    reasoning_output_tokens: 0
  }
  errors=NONE

turn-08-filler.jsonl:
  thread.started=1
  turn.started=1
  error=1
  turn.failed=1
  usage=NONE
  error="stream disconnected before completion: idle timeout waiting for SSE"
```

Therefore the runner's JSONL parser is not the reason for the printed `INPUT_TOKENS=0`: the live Codex `turn.completed.usage` object itself contains zeros on this UWA provider path. Usage must be treated as unavailable instrumentation for this gate rather than as a measurement of context growth.

The eighth turn's direct Codex failure is now classified as an SSE idle timeout, not as a proven context-limit or compaction error.

## Compact evidence boundary

The bounded UWA log keyword scan found compact lines, but those are historical lines from earlier P1.1 work, including the already-known stale-runtime logger traces and the earlier successful direct compact probe.

No new run-scoped `/v1/responses/compact` success evidence was established for this P1.2 run.

The acceptance runner also has a real failure-path evidence bug: `_run_codex_turn()` raises on non-zero exit status and the outer filler loop returns before `scan_log_delta()` runs for the failed turn. Thus rounds 1-7 have explicit zero compact deltas, while round 8 currently has no harvested run-scoped compact delta.

Do not infer either of the following from the current evidence:

- that round 8 definitely attempted compact;
- that round 8 definitely did not attempt compact.

Compaction remains unproven for this live run.

## What is proven

- Seed contract passed.
- Seven filler continuations returned exact ACKs with zero observed local tool effects.
- Successful Codex JSONL turns report a zeroed usage object on this provider path.
- Round 8 failed with `stream disconnected before completion: idle timeout waiting for SSE`.
- Current UWA listener remained healthy after the failure and reported browser connected.
- No current-run compact success is proven.
- P1.2 live remains BLOCKED and no compaction PASS is claimed.

## Current engineering gate

Do not rerun the full 24-round acceptance yet.

Next diagnosis must inspect the UWA-side request lifecycle for the failed turn and distinguish among:

1. ChatGPT Web/model generation stalled long enough that Codex hit its configured SSE idle timeout;
2. UWA received/generated a result but failed to emit SSE activity/completion downstream;
3. a hidden compact/request transition occurred but the runner missed the failed-turn log delta;
4. another browser/request-path failure caused the stream to go silent.

The next diagnostic should use a bounded run-time window or newly appended log slice rather than searching historical compact lines across the whole log.

After the UWA-side failure path is identified, first repair acceptance instrumentation so failed turns harvest their log delta, then fix the actual runtime blocker before rerunning P1.2.
