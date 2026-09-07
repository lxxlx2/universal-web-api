# P1.2 remote compaction V2 protocol gap — 2026-09-08

## Scope

Pre-live protocol audit after the narrow Codex 0.153.4 remote-compaction capability shim passed CI.

The exact remote V2 compact contract was compared with UWA's already-live P1.1 compact endpoint before touching the real macOS provider config.

## Exact Codex 0.153.4 contract

Exact release:

```text
rust-v0.153.4
3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

Important correction from the first draft of this record: `/responses/compact` itself is **unary HTTP**, not an SSE endpoint. The exact client source explicitly documents this and calls `CompactClient.compact_input(...)` with a full-response timeout.

The remote V2 core appends a request-only `compaction_trigger`, invokes the unary compact endpoint through `ModelClientSession`, and receives `output: Vec<ResponseItem>`. Codex then internally exposes those items to the V2 collector as response events.

The V2 collector accepts the attempt only when exactly one returned output item deserializes as:

```text
ResponseItem::Compaction
```

The required unary wire shape is therefore equivalent to:

```json
{
  "output": [
    {
      "type": "compaction",
      "encrypted_content": "<opaque compaction payload>"
    }
  ]
}
```

If exactly one compaction item is not present, Codex returns a fatal protocol error.

## Current UWA compact contract

`app/api/codex_compact.py` currently implements a legacy unary replacement-history adapter. It:

1. converts compact history into a no-tools ChatGPT Web summarization request;
2. builds a normal assistant Responses message;
3. returns unary JSON containing assistant message item(s).

This P1.1 contract is already proven by direct macOS HTTP validation, but its output item type is not the Codex 0.153.4 remote V2 type.

## Consequence

The Azure-name capability shim is necessary for native Codex to select remote compaction, but it is not sufficient.

Against the current endpoint the predictable sequence would be:

```text
native threshold reached
→ Codex selects remote V2
→ unary POST /v1/responses/compact reaches UWA
→ UWA returns output=[assistant message]
→ Codex V2 receives zero Compaction items
→ remote compaction fails
```

Therefore the real macOS capability shim remains disabled until the item-shape/continuity repair is green.

## Required repair

Keep P1.1 legacy unary behavior for requests without the V2 trigger. For a compact request containing `compaction_trigger`:

1. remove the request-only trigger before web summarization;
2. generate the same bounded no-tools ChatGPT Web summary;
3. encode that summary in a UWA-owned bounded opaque compaction envelope;
4. return unary `output` with exactly one `type=compaction` item carrying that envelope in `encrypted_content`;
5. teach ordinary UWA Codex Responses browser translation to decode only UWA-owned compaction envelopes back into model-visible compacted context;
6. fail closed on unknown/corrupt envelopes rather than silently dropping context;
7. keep compact content private and never log the envelope or summary body.

The schema field name `encrypted_content` is upstream terminology. UWA must not claim that its local envelope is OpenAI encryption. The local envelope is only opaque transport state with explicit bounds/integrity checks.

## Continuity note

Codex records the compact response ID as compaction metadata, but its compact request/response transport remains unary. The next implementation must preserve client-supplied compacted history semantics; it must not rely on the browser model understanding an OpenAI encrypted blob. UWA therefore needs its own envelope decode step when a later normal Responses input contains the returned compaction item.

## Regression requirements

- legacy P1.1 unary assistant-message behavior stays green;
- V2 detection requires a `compaction_trigger` item;
- trigger is not sent to the backing web model;
- V2 unary response contains exactly one `type=compaction` item;
- UWA envelope round-trip preserves Unicode summary text;
- corrupted/foreign compaction envelope fails closed;
- ordinary browser translation rewrites a UWA compaction item into an assistant compact-context message without exposing the raw envelope;
- no tools are available during compact summarization;
- compact summary/envelope contents are never logged;
- public-repo safety remains green.

## Gate

Do not run the native remote-compaction macOS test until the unary V2 item/envelope repair and CI are green.
