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

## Initial UWA gap and live probe

Code inspection found no registered `/v1/responses/compact` endpoint. The macOS operator then probed the running UWA instance directly after confirming `/health` was healthy.

Observed non-sensitive evidence:

```text
COMPACT_ROUTE_REGISTERED=NO
HTTP/1.1 404 Not Found
content-type: application/json
{"error":{"message":"接口不存在","path":"/v1/responses/compact"}}
```

This closed P1.0 with code inspection and deployed-runtime evidence agreeing: the compact endpoint was genuinely absent.

## P1.1 implementation and CI

The branch added:

```text
app/api/codex_compact.py
tests/test_codex_responses_compact.py
```

The route is registered before normal Responses handling. It is designed to:

- accept `POST /v1/responses/compact`;
- preserve the incoming model/reasoning context instead of pinning a different model;
- disable client tools during compaction;
- ask the configured ChatGPT Web model for a concise replacement-history summary;
- return only valid assistant Responses message items in `{"output": [...]}`;
- reject function-call-only backing output;
- avoid fabricating OpenAI encrypted compaction blobs;
- return structured errors on backing failures.

Regression coverage checks route registration, model/reasoning preservation, tool suppression, assistant-message output and rejection of function-call-only output.

GitHub Actions `Security hardening` run #220 for implementation/test head `5cccbcf4b7f5f0c53467423ce1e5250c7fc1457d` completed with `success`.

## Post-implementation live result: FAIL

After pulling the implementation, restarting UWA and confirming health, the operator observed:

```text
COMPACT_ROUTE_REGISTERED=YES
COMPACT_HTTP_CODE=500
JSON_PARSE=PASS
OUTPUT_IS_LIST=NO
OUTPUT_COUNT=0
MARKER_PRESERVED=NO
TASK_PRESERVED=NO
```

The synthetic probe used harmless marker `ALPHA-42` and asked the compact path to preserve the current compact-protocol task.

This means registration and helper-level regression coverage are insufficient. The real FastAPI/backing-response path still has an unhandled runtime exception. P1.1 remains open and P1.2 large-context stress remains blocked.

A dedicated incident record is in `docs/CODEX_P1_COMPACT_LIVE_500_2026-09-07.md`.

## Current diagnostic hypothesis

In `app/api/codex_compact.py`, web-mode preparation and `_run_chat_completion_final()` are already inside an exception boundary that converts exceptions to structured `502` responses. The observed raw `500` therefore points more strongly to an exception before that block or after the backing request, such as request adaptation, payload sanitization, output conversion, or another route-level path.

This is explicitly a hypothesis until the local UWA traceback is inspected.

## Classification

This remains a P1 protocol-hardening item, not a regression in Stage A-F.

```text
Stage A-F live acceptance             PASS
aggregate A-F checker                 PASS
P1 compact contract inspection        DONE
initial runtime compact probe         DONE: 404 confirmed
compact endpoint implementation       DONE
compact regression + CI               PASS
post-implementation runtime probe     FAIL: HTTP 500
traceback / route-level reproduction  CURRENT
large-context stress/recovery         BLOCKED
Desktop UI live gate                  required before main merge
```

## Next sequence

1. extract only the relevant local UWA traceback around the compact request;
2. reproduce the exact failing route-level path in regression coverage;
3. implement the smallest repair;
4. require CI green;
5. rerun the same direct compact call and require HTTP 200 plus an assistant message inside `output`;
6. add the synthetic large-context workload;
7. require an observable compaction lifecycle item plus post-compaction context recovery;
8. deepen lost-affinity/restart validation;
9. run the mandatory Desktop UI live gate before the real-project/final merge gate.

No private runtime state, conversation identifiers, cookies, logs or Responses SQLite contents are included in this record.
