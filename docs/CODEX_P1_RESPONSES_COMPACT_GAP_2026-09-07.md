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

## UWA branch inspection and live probe

Code inspection found no registered `/v1/responses/compact` endpoint. The macOS operator then probed the running UWA instance directly after confirming `/health` was healthy.

Observed non-sensitive evidence:

```text
COMPACT_ROUTE_REGISTERED=NO
HTTP/1.1 404 Not Found
content-type: application/json
{"error":{"message":"接口不存在","path":"/v1/responses/compact"}}
```

This closed P1.0 with code inspection and deployed-runtime evidence agreeing: the compact endpoint was genuinely absent.

## P1.1 implementation

The branch now includes:

```text
app/api/codex_compact.py
tests/test_codex_responses_compact.py
```

The route is registered before normal Responses handling. It:

- accepts `POST /v1/responses/compact`;
- preserves the incoming model/reasoning context instead of pinning a different model;
- disables client tools during compaction;
- asks the configured ChatGPT Web model for a concise replacement-history summary;
- returns only valid assistant Responses message items in `{"output": [...]}`;
- rejects function-call-only backing output;
- does not fabricate OpenAI encrypted compaction blobs;
- returns structured errors on backing failures.

Regression coverage checks route registration, model/reasoning preservation, tool suppression, assistant-message output and rejection of function-call-only output.

GitHub Actions `Security hardening` run #220 for implementation/test head `5cccbcf4b7f5f0c53467423ce1e5250c7fc1457d` completed with `success`.

## Classification

This remains a P1 protocol-hardening item, not a regression in Stage A-F.

The code path and CI are now green. The next gate is a direct macOS runtime probe after pulling the implementation and restarting UWA. Large-context stress remains blocked until that live unary compact call succeeds and returns usable replacement history.

## Next sequence

1. restart the local UWA on the current branch and verify OpenAPI registers `/v1/responses/compact`;
2. perform one direct compact call with a harmless marker and verify HTTP 200 plus an assistant message inside `output`;
3. record the live result;
4. add the synthetic large-context workload;
5. require an observable compaction lifecycle item plus post-compaction context recovery;
6. deepen lost-affinity/restart validation;
7. run the mandatory Desktop UI live gate before the real-project/final merge gate.

## Status

```text
Stage A-F live acceptance             PASS
aggregate A-F checker                 PASS
P1 compact contract inspection        DONE
initial runtime compact probe         DONE: 404 confirmed
compact endpoint implementation       DONE
compact regression + CI               PASS
post-implementation runtime probe     NEXT
large-context stress/recovery         blocked on live compact acceptance
Desktop UI live gate                  required before main merge
```

No private runtime state, conversation identifiers, cookies, logs or Responses SQLite contents are included in this record.
