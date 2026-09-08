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

- legacy remote compaction uses unary `/responses/compact` through `compact_conversation_history()` / `CompactClient.compact_input(...)`;
- remote compaction V2 does not use that unary endpoint;
- `run_remote_compact_v2_attempt()` appends a request-only `compaction_trigger` and calls `ModelClientSession.stream()`;
- UWA has `wire_api=responses` and WebSockets disabled, so remote V2 uses ordinary HTTP Responses at `/v1/responses`.

## Exact remote V2 response contract

The V2 collector accepts the attempt only when exactly one output item deserializes as:

```text
ResponseItem::Compaction
```

Equivalent item:

```json
{
  "type": "compaction",
  "encrypted_content": "<opaque compaction payload>"
}
```

The request-side `compaction_trigger` is control state and must not become model-visible durable history.

## Implemented repair

The ordinary Codex Responses bridge now:

1. validates exactly one trailing `compaction_trigger` and rejects malformed placement;
2. removes the request-only trigger before browser translation;
3. disables tools/tool choice during bounded ChatGPT Web compaction summarization;
4. encodes the summary into a versioned, bounded, integrity-checked UWA-owned opaque envelope;
5. emits exactly one `type=compaction` output item and a valid `response.completed` with non-zero usage;
6. decodes only valid UWA-owned envelopes into model-visible compact context on future client-replayed history;
7. rejects foreign/corrupt/oversized envelopes fail-closed;
8. never logs summary/envelope bodies.

The upstream field name is `encrypted_content`; UWA does not claim its local envelope is OpenAI encryption.

## Continuity semantics

Exact 0.153.4 HTTP `ResponsesApiRequest` has no `previous_response_id` field. The recorded `compaction_response_id` is therefore Codex-side checkpoint metadata, not a server continuation handle. After compaction, Codex replays compacted history on later HTTP turns, and UWA reconstructs model-visible compact context from the replayed envelope.

## Tracked implementation

- `app/services/codex_remote_compaction_v2.py`
- `tests/test_codex_remote_compaction_v2.py`
- installation ordering in `app/api/routes.py`
- `tools/codex_remote_compaction_trigger_probe.py`
- `tests/test_codex_remote_compaction_trigger_probe.py`

## CI history

Attempt #372 / run `34184935625`:

```text
new V2 module py_compile      PASS
public-repo-safety            PASS
focused test collection       FAIL: security matrix lacked full runtime dependencies
```

The runtime-level test was moved to the existing `upstream-regression` job, which installs `requirements.txt`.

Attempt #378 / run `34185372863`:

```text
492 passed
1 failed: probe-wrapper test imported the same support module under two Python module names
```

That acceptance-test import-identity defect was repaired.

Attempt #380 / run `34185500715`:

```text
public-repo-safety                  PASS
security-tests macOS 3.11 / 3.13   PASS
security-tests Ubuntu 3.11 / 3.13  PASS
upstream reproducible regression   PASS
```

The protocol repair is therefore implementation/CI PASS.

## Current gate

Run the native remote-compaction macOS acceptance with the fail-closed capability helper enabled for a fresh Codex CLI process. Required evidence:

```text
THRESHOLD_CROSSED=YES
PRE_TRIGGER_OVER_HARD_CAP=NO
ROLLOUT_COMPACT_MARKER_DELTA>=1
REMOTE_COMPACT_ROUTE_DELTA>=1
REMOTE_COMPACT_SUCCESS_DELTA>=1
AUTO_COMPACT_MODE=REMOTE
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

After this gate, P1.2 still requires same-thread post-remote-compaction recovery of the conversation-only synthetic token through a real local write/read.
