# P1.2 second real macOS large-context failure — 2026-09-08

## Status

FAIL / DIAGNOSIS CURRENT.

This checkpoint records the second full real macOS P1.2 large-context run after the stream heartbeat and Responses usage compatibility repair.

## Runtime precondition

The repaired UWA runtime was healthy and browser-connected before the run. The preceding live smoke had already proven non-zero Codex usage accounting on the same repaired implementation.

## Observed run

The synthetic conversation-only token seed succeeded with no local tool effects. The same Codex thread then completed seven deterministic filler continuations. Reported Codex input usage grew as follows:

```text
round 01  21230
round 02  42219
round 03  70125
round 04 104948
round 05 146688
round 06 195345
round 07 250919
```

Every completed filler round preserved the no-tool-effect contract.

However, across rounds 1-7 the current-run compact evidence remained:

```text
COMPACT_ROUTE_DELTA=0
COMPACT_SUCCESS_DELTA=0
```

Round 8 then failed the filler contract:

```text
ACK_EXACT=NO
TOOL_EFFECTS=0
INPUT_TOKENS=-1
COMPACT_ROUTE_DELTA=0
COMPACT_SUCCESS_DELTA=0
RUN_FAIL filler_contract round=8
```

## Interpretation boundary

This run proves that the previous two transport blockers are repaired in the live runtime:

1. successful turns now expose positive, growing usage instead of all-zero usage;
2. the run survives beyond the former round-8 SSE idle-timeout failure point far enough to complete seven large continuations.

It does **not** prove native compaction. The declared model context window is 64000, yet reported input usage exceeded that value from round 3 onward without any current-run `/v1/responses/compact` route or success marker.

Therefore the next task is to inspect the actual upstream Codex auto-compaction trigger conditions and UWA model metadata/config contract. Do not blindly increase filler volume or rerun the same full stress test before that trigger path is understood.

## Safety

No private Codex JSONL, prompts, token value, browser/session identifiers, local process identifiers, cookies, credentials, workspace source, or private UWA logs are committed in this record.
