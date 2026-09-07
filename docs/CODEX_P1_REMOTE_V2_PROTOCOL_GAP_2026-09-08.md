# P1.2 remote compaction V2 protocol gap — 2026-09-08

## Scope

Pre-live protocol audit after the narrow Codex 0.153.4 remote-compaction capability shim passed CI.

The intent was to enable the capability shim and rerun the small-step threshold probe. Before touching the real macOS config, the exact remote V2 response contract was compared with UWA's already-live P1.1 compact endpoint.

## Exact Codex 0.153.4 V2 contract

Exact release:

```text
rust-v0.153.4
3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

`run_remote_compact_v2_attempt()` appends a request-only `compaction_trigger` item and executes the request through the streaming Responses client.

The response collector counts `response.output_item.done` items and accepts the attempt only when exactly one item deserializes as:

```text
ResponseItem::Compaction
```

The wire shape is equivalent to:

```json
{
  "type": "response.output_item.done",
  "item": {
    "type": "compaction",
    "encrypted_content": "<opaque compaction payload>"
  }
}
```

If exactly one compaction output item is not present, Codex returns a fatal protocol error.

## Current UWA compact contract

`app/api/codex_compact.py` is explicitly a legacy unary replacement-history adapter. It currently:

1. converts compact history into a no-tools ChatGPT Web summarization request;
2. builds a normal assistant Responses message;
3. returns unary JSON:

```json
{
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": ["..."]
    }
  ]
}
```

This is the P1.1 contract already proven by direct macOS HTTP validation, but it is not the Codex 0.153.4 remote V2 stream contract.

## Consequence

The Azure-name capability shim is necessary for native Codex to select remote compaction, but it is not sufficient.

Enabling it against the current endpoint would predictably produce this sequence:

```text
native auto-compact threshold reached
→ Codex selects remote V2
→ POST /v1/responses/compact reaches UWA
→ UWA returns legacy assistant-message unary shape
→ Codex V2 sees zero Compaction output items / wrong transport shape
→ remote compaction fails
```

Therefore the real macOS capability shim must not be enabled yet.

## Required repair

P1.1 legacy unary behavior must remain compatible. Add a V2 path when the compact request is the streaming compaction-trigger form:

1. generate the same bounded ChatGPT Web summary;
2. encode that summary in a UWA-owned opaque compaction envelope;
3. emit real Responses SSE including one `type=compaction` output item;
4. emit a completed response event;
5. teach ordinary UWA Codex Responses browser translation to decode only UWA-owned compaction envelopes back into model-visible compacted context;
6. fail closed on unknown/non-UWA opaque compaction payloads rather than silently dropping context;
7. keep all compact content private and never log the envelope or summary body.

The field name `encrypted_content` comes from the Codex Responses schema. UWA must not falsely claim its local envelope is OpenAI encryption. The envelope should be treated as opaque transport state with integrity/bounds, stored only wherever Codex already stores private rollout history.

## Regression requirements

- legacy unary P1.1 tests remain green;
- V2 detection requires the streaming compaction-trigger contract;
- V2 emits exactly one compaction item;
- V2 output is parseable as SSE and terminates with `response.completed`;
- UWA envelope round-trip preserves Unicode summary text;
- corrupted/foreign compaction envelope fails closed;
- browser translation rewrites UWA compaction into an assistant compact-context message without exposing the raw envelope;
- no tools are available during compact summarization;
- heartbeat remains a parseable `response.in_progress` event for long web-backed compaction;
- public-repo safety remains green.

## Gate

Do not run the native remote-compaction macOS test until the V2 protocol repair and CI are green.
