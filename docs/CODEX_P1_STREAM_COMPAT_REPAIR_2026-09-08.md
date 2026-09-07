# P1.2 Codex stream compatibility repair — 2026-09-08

## Status

IMPLEMENTED / CI PASS / LIVE VALIDATION PENDING.

This checkpoint follows the first real macOS P1.2 large-context run, which completed the seed and seven filler continuations before round 8 failed with:

```text
stream disconnected before completion: idle timeout waiting for SSE
```

The UWA listener remained healthy and browser-connected after the client failure.

## Confirmed protocol gaps

### 1. SSE comments do not reset Codex's idle timer

The bridge previously emitted comment heartbeats while the browser-backed request was still running:

```text
: keepalive
```

Current upstream Codex waits for the next **parsed SSE event** under its idle timeout. EventSource comments are transport bytes but are discarded by the parser, so comment-only traffic does not satisfy that timer.

Upstream Codex also explicitly accepts `response.in_progress` as a Responses event and ignores it at the semantic layer. Therefore the bridge now converts transport heartbeats into a real parseable event:

```text
event: response.in_progress
data: {"type":"response.in_progress"}
```

This keeps the stream semantically inert while providing real SSE activity to the Codex parser during long ChatGPT Web reasoning.

### 2. Zero Responses usage prevents native auto-compaction

The live Codex JSONL from successful P1.2 turns contained a real `turn.completed.usage` object, but every field was zero:

```text
input_tokens=0
cached_input_tokens=0
cache_write_input_tokens=0
output_tokens=0
reasoning_output_tokens=0
```

Upstream Codex auto-compaction checks the session's accumulated token usage when deciding whether the configured context/auto-compact threshold has been reached. With zero usage on every completed response, the Codex client sees an active context of zero tokens and cannot naturally reach that threshold.

ChatGPT Web does not currently provide the OpenAI Responses token accounting needed by Codex, so the bridge now supplies a conservative local usage estimate **only when upstream usage is missing or zero**. Any future real non-zero usage is preserved exactly and takes precedence.

The estimator:

- is process-local and metadata-only;
- uses a conservative three UTF-8 bytes per token approximation;
- keeps a bounded `response_id -> total_tokens` map so continuation totals grow monotonically;
- charges only the new continuation input after a previous response total is known;
- never logs or persists prompt text, tool arguments, response text, cookies, credentials or workspace contents;
- logs only numeric estimated counts.

## Implementation

Added:

- `app/services/codex_stream_compat.py`
- `tests/test_codex_stream_compat.py`

`app/api/routes.py` installs the compatibility layer after existing V2 runtime hardening so it wraps the final Codex streaming path.

The layer covers both the V2 browser/tool stream and the legacy minimal Codex Responses stream.

Regression coverage verifies:

1. heartbeat is a real `response.in_progress` SSE event rather than a comment;
2. zero/missing usage is replaced with positive conservative accounting;
3. continuation usage grows through `previous_response_id`;
4. real non-zero usage is never overwritten;
5. unrelated non-terminal Responses events are unchanged.

## CI

Implementation head:

```text
f23a475a67df56514a660e935165c35a3dcd9e43
```

Security hardening workflow:

```text
run #308
id 34153827846
status completed
conclusion success
```

This covers the macOS/Ubuntu security matrix, reproducible upstream regression suite and public-repository-safety gate.

## Remaining acceptance instrumentation gap

The P1.2 runner currently raises immediately when a Codex turn exits non-zero. The outer loop therefore does not harvest the UWA log delta for that failed turn. This must be repaired before the next full P1.2 run so a failure cannot hide compact lifecycle evidence from the same round.

## Next gate

Do not immediately repeat the full 24-round stress run.

Required order:

1. repair failed-turn log harvesting in the P1.2 acceptance path;
2. restart UWA so the new stream compatibility code is actually loaded;
3. run a small live smoke proving a normal Codex completion now reports non-zero usage;
4. only then rerun the full native compact/recovery acceptance.

P1.2 remains open until real macOS evidence proves both stream survival and native `/v1/responses/compact` behavior.
