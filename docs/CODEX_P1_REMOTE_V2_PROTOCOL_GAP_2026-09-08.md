# P1.2 remote compaction V2 protocol gap — 2026-09-08

## Scope

Pre-live protocol audit after the narrow Codex 0.153.4 remote-compaction capability shim passed CI.

The exact remote V2 request/response path was traced before touching the real macOS provider config.

## Exact Codex 0.153.4 routing

Exact release:

```text
rust-v0.153.4
3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

Important correction to earlier drafts of this record:

- legacy remote compaction uses unary `/responses/compact` through `compact_conversation_history()` / `CompactClient.compact_input(...)`;
- **remote compaction V2 does not use that unary endpoint**;
- `run_remote_compact_v2_attempt()` appends a request-only `compaction_trigger` to the prompt and calls `ModelClientSession.stream()`;
- for the configured UWA `wire_api=responses` provider with WebSockets disabled, `ModelClientSession.stream()` enters the ordinary HTTP Responses transport;
- therefore native remote V2 reaches the normal provider Responses endpoint (`/v1/responses`), not `/v1/responses/compact`.

This distinction is exact-release behavior, not an inference from endpoint names.

## Exact remote V2 response contract

The V2 collector consumes the ordinary Responses stream and accepts the compact attempt only when exactly one `response.output_item.done` item deserializes as:

```text
ResponseItem::Compaction
```

Equivalent Responses item shape:

```json
{
  "type": "compaction",
  "encrypted_content": "<opaque compaction payload>"
}
```

If the collector receives zero or more than one `Compaction` item, Codex returns a fatal protocol error.

The request-side `compaction_trigger` is a control item and must not become durable model-visible conversation content.

## Current UWA behavior

Current ordinary UWA Codex Responses handling translates normal Responses input into ChatGPT Web messages and emits normal assistant `message` / `function_call` items. It does not yet implement a dedicated `compaction_trigger` request path or emit a `type=compaction` item.

P1.1 remains valid but is a separate legacy endpoint proof: `POST /v1/responses/compact` unary assistant replacement-history output works directly. That does not satisfy Codex 0.153.4 remote V2 because V2 runs through ordinary `/v1/responses`.

## Consequence

The Azure-name capability shim is necessary for Codex 0.153.4 to select remote V2, but enabling it now would predictably fail:

```text
native threshold reached
→ Codex selects remote V2
→ ordinary POST /v1/responses with trailing compaction_trigger
→ UWA treats it as a normal Responses turn
→ no Compaction output item is emitted
→ Codex V2 collector fails exact-one-Compaction contract
```

Therefore the real macOS capability shim remains disabled until the ordinary Responses V2 compaction protocol repair is green.

## Required repair

Implement the V2 path in the ordinary Codex Responses bridge, not in the legacy unary compact route:

1. detect exactly one trailing `compaction_trigger` in a remote-compaction request;
2. reject malformed/ambiguous trigger placement fail-closed;
3. remove the request-only trigger before constructing model-visible ChatGPT Web history;
4. disable client tools/tool choice for the backing compaction summarization;
5. generate the same bounded durable-thread summary through ChatGPT Web;
6. encode that summary into a UWA-owned bounded opaque envelope with versioning and integrity validation;
7. emit normal Responses SSE containing exactly one `response.output_item.done` with `type=compaction` and the envelope in `encrypted_content`;
8. emit a valid terminal `response.completed` with non-zero bounded usage compatible with Codex TokenCount accounting;
9. on later ordinary Responses input, decode only valid UWA-owned compaction envelopes into model-visible compact context before browser translation;
10. reject foreign/corrupt/oversized envelopes rather than silently dropping or exposing opaque content;
11. never log the summary or envelope body.

The upstream field name is `encrypted_content`. UWA does not claim that its own local envelope is OpenAI encryption; it is only opaque transport state for this local compatibility bridge.

## Continuity requirements

Codex installs the returned Compaction item into replacement history. Exact 0.153.4 HTTP `ResponsesApiRequest` has no `previous_response_id` field, so the saved `compaction_response_id` is Codex-side checkpoint metadata rather than a server continuation handle. The next ordinary HTTP turn replays the compacted client history. UWA therefore reconstructs model-visible compact context directly from the replayed UWA-owned envelope.

This keeps post-compact recovery independent of an in-memory-only summary map or a compact-response ID registration step. Existing private Responses persistence and web-session affinity remain useful for the broader bridge, but remote-V2 summary recovery itself is carried by the client-replayed compacted history.

## Regression requirements

- P1.1 legacy `/v1/responses/compact` behavior remains unchanged and green;
- ordinary V2 request detection requires exactly one valid trailing `compaction_trigger`;
- malformed trigger input fails closed;
- trigger never reaches ChatGPT Web as conversation content;
- tools are unavailable during compaction summarization;
- V2 stream emits exactly one `type=compaction` output item;
- completed response is valid and includes non-zero usage;
- UWA envelope round-trip preserves Unicode summary text;
- corrupted, foreign and oversized envelopes fail closed;
- later normal browser translation decodes a valid UWA compaction item into model-visible compact context without exposing raw envelope data;
- summary/envelope contents are never written to public logs or tracked files;
- public-repo safety remains green.

## Implementation checkpoint

Tracked implementation now exists in:

- `app/services/codex_remote_compaction_v2.py`
- `tests/test_codex_remote_compaction_v2.py`
- installation ordering in `app/api/routes.py`
- `tools/codex_remote_compaction_trigger_probe.py` for V2-specific live evidence

CI attempt #372 / run `34184935625` proved the new V2 module compiled and public-repository safety passed, then failed during focused-test collection because the lightweight security matrix intentionally lacked FastAPI/runtime dependencies. The tests were moved to the existing full-dependency `upstream-regression` job.

CI attempt #378 / run `34185372863` then executed the full reproducible regression suite: 492 tests passed and one new acceptance-wrapper test failed. The failure was an import-identity defect in the test itself: the same `codex_large_context_acceptance.py` file had been loaded once as `tools.codex_large_context_acceptance` and once as top-level `codex_large_context_acceptance`, producing two Python module objects. The wrapper and delegated trigger probe use the same top-level module at runtime; the test incorrectly compared that state with the separately imported package module. This is classified as acceptance-test plumbing, not a V2 protocol failure.

## Gate

Do not run the native remote-compaction macOS test until the ordinary Responses V2 compaction path, regression suite and CI are green.
