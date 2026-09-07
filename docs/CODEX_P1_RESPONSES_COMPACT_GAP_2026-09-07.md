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

## Post-implementation live result: FAIL, root cause confirmed

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

The traceback then identified the exact failure:

```text
TypeError: SecureLogger.info() takes 2 positional arguments but 3 were given
```

The compact backing request and assistant replacement output had already succeeded. The request failed only when `app/api/codex_compact.py` tried to log success using stdlib logging interpolation arguments. UWA's `SecureLogger.info()` accepts exactly one message argument.

The same incompatible pattern also existed on the backing-error `logger.warning()` branch and was repaired proactively.

A dedicated incident record is in `docs/CODEX_P1_COMPACT_LIVE_500_2026-09-07.md`.

## Repair

The narrow repair:

- changes compact success/error logging to single preformatted messages;
- adds full route-level success coverage with a one-argument logger;
- adds full backing-error route coverage with a one-argument logger;
- keeps all compaction protocol behavior otherwise unchanged.

Repair commit: `2e1a1f36960a253d67e105e6a0da84d0a7b56fe5`.

## Classification

This remains a P1 protocol-hardening item, not a regression in Stage A-F.

```text
Stage A-F live acceptance             PASS
aggregate A-F checker                 PASS
P1 compact contract inspection        DONE
initial runtime compact probe         DONE: 404 confirmed
compact endpoint implementation       DONE
pre-repair compact regression + CI    PASS
post-implementation runtime probe     FAIL: HTTP 500
traceback root cause                  CONFIRMED: SecureLogger signature
narrow repair + route regressions     DONE
repair CI                             NEXT
post-repair macOS live rerun          blocked on CI
large-context stress/recovery         BLOCKED
Desktop UI live gate                  required before main merge
```

## Next sequence

1. require repair CI green;
2. rerun the exact same direct compact call and require HTTP 200 plus an assistant message inside `output`;
3. add the synthetic large-context workload;
4. require an observable compaction lifecycle item plus post-compaction context recovery;
5. deepen lost-affinity/restart validation;
6. run the mandatory Desktop UI live gate before the real-project/final merge gate.

No private runtime state, conversation identifiers, cookies, logs or Responses SQLite contents are included in this record.
