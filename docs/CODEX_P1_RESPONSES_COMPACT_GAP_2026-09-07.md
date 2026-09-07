# P1 Responses compact protocol gap — 2026-09-07

## Context

Stage A-F live acceptance and the repaired aggregate checker are PASS. P1 now moves to large-context compaction / stress / recovery.

Before generating a large synthetic context, the compaction transport contract was checked against current upstream Codex behavior.

## Upstream Codex contract

Current Codex remote compaction uses:

```text
POST /v1/responses/compact
```

The canonical request includes the active model, canonical response-item input, instructions and applicable tool/reasoning/text controls. The compact client parses a JSON response containing an `output` array of Responses items.

Recent Codex exec/app-server behavior also exposes compaction as an explicit context-compaction lifecycle item, so P1 can eventually require observable compaction evidence rather than inferring success from a long conversation alone.

Relevant upstream source locations:

```text
openai/codex: codex-rs/codex-api/src/endpoint/compact.rs
openai/codex: codex-rs/codex-api/src/common.rs
openai/codex: codex-rs/app-server/tests/suite/v2/compaction.rs
```

## UWA branch inspection

Current `codex-web-bridge-v2` has normal Responses handling in:

```text
app/api/codex_responses_v2.py
app/api/codex_responses.py
app/api/chat.py
```

The route inspection found no registered `/v1/responses/compact` endpoint.

## Live runtime probe

The macOS operator then probed the running UWA instance directly after confirming `/health` was healthy.

Observed non-sensitive evidence:

```text
COMPACT_ROUTE_REGISTERED=NO
HTTP/1.1 404 Not Found
content-type: application/json
{"error":{"message":"接口不存在","path":"/v1/responses/compact"}}
```

This closes P1.0 with code inspection and deployed-runtime evidence agreeing: the compact endpoint is genuinely absent.

## Classification

This is a P1 protocol blocker, not a regression in Stage A-F.

Long sessions may work until Codex decides remote compaction is required. At that point an OpenAI-compatible provider is expected to service `/v1/responses/compact`; a missing endpoint can terminate the long-running session instead of recovering it.

## Next sequence

1. implement the smallest compatible compact endpoint with unit/regression coverage;
2. verify CI and direct compact protocol acceptance;
3. add the synthetic large-context workload;
4. require an observable compaction lifecycle item plus post-compaction context recovery;
5. deepen lost-affinity/restart validation;
6. run the mandatory Desktop UI live gate before the real-project/final merge gate;
7. keep real-project long-task testing blocked until the synthetic compaction path passes.

## Status

```text
Stage A-F live acceptance             PASS
aggregate A-F checker                 PASS
P1 compact contract inspection        DONE
UWA /v1/responses/compact route       ABSENT CONFIRMED
local runtime compact probe           DONE: 404 confirmed
compact endpoint implementation       IN PROGRESS
large-context stress/recovery         blocked on compact protocol support
Desktop UI live gate                  required before main merge
```

No private runtime state, conversation identifiers, cookies, logs or Responses SQLite contents are included in this record.
