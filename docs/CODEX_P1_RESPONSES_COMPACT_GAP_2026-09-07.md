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

## P1.1 implementation and first live failure

The branch added:

```text
app/api/codex_compact.py
tests/test_codex_responses_compact.py
```

The first post-implementation macOS probe showed that the route was now registered, but the live call returned HTTP 500:

```text
COMPACT_ROUTE_REGISTERED=YES
COMPACT_HTTP_CODE=500
JSON_PARSE=PASS
OUTPUT_IS_LIST=NO
OUTPUT_COUNT=0
MARKER_PRESERVED=NO
TASK_PRESERVED=NO
```

The first traceback identified:

```text
TypeError: SecureLogger.info() takes 2 positional arguments but 3 were given
```

The backing ChatGPT Web compact request and non-empty assistant replacement output had already succeeded. Only the final success log failed because the new endpoint used stdlib logging interpolation arguments against UWA's one-argument `SecureLogger.info()`. The backing-error `logger.warning()` path had the same latent incompatibility.

Detailed incident: `docs/CODEX_P1_COMPACT_LIVE_500_2026-09-07.md`.

## First repair and CI

The active branch contains the narrow first repair:

- success logging uses one preformatted message argument;
- backing-error logging uses one preformatted message argument;
- route-level success regression uses a logger exposing only `info(message)`;
- route-level backing-error regression uses a logger exposing only `warning(message)`;
- compaction protocol semantics are otherwise unchanged.

Security hardening CI #239 for repair code commit `7c6d7ff` completed successfully.

## Post-repair live rerun

The operator pulled through `b3f37ac`, verified the repaired logger line locally, restarted UWA, confirmed `/health`, confirmed the compact route, and reran the unchanged direct probe.

Observed result:

```text
COMPACT_ROUTE_REGISTERED=YES
COMPACT_HTTP_CODE=500
JSON_PARSE=PASS
OUTPUT_IS_LIST=NO
OUTPUT_COUNT=0
MARKER_PRESERVED=NO
TASK_PRESERVED=NO
```

The first logger defect is fixed and deployed, but this live result proves that P1.1 still contains a second unhandled runtime path. Its root cause is unknown until a fresh post-repair traceback is inspected.

## Classification

This remains a P1 protocol-hardening item, not a regression in Stage A-F.

```text
Stage A-F live acceptance             PASS
aggregate A-F checker                 PASS
P1 compact contract inspection        DONE
initial runtime compact probe         DONE: 404 confirmed
compact endpoint implementation       DONE
first post-implementation live probe  FAIL: HTTP 500
first traceback root cause            CONFIRMED: SecureLogger signature
first repair + route regressions      DONE
first repair CI                       PASS: #239
post-repair live rerun                FAIL: HTTP 500
second traceback root cause           CURRENT / UNKNOWN
large-context stress/recovery         BLOCKED until live compact PASS
Desktop UI live gate                  required before main merge
```

## Next sequence

1. extract the fresh local traceback for the post-repair compact request;
2. reproduce the exact second failing path in route-level coverage;
3. implement the smallest repair;
4. require CI green;
5. rerun the unchanged direct compact call and require HTTP 200 plus an assistant message inside `output`;
6. add the synthetic large-context workload;
7. require an observable compaction lifecycle item plus post-compaction context recovery;
8. deepen lost-affinity/restart validation;
9. run the mandatory Desktop UI live gate before the real-project/final merge gate.

No private runtime state, conversation identifiers, cookies, logs or Responses SQLite contents are included in this record.
