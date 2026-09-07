# P1.2 Codex stream compatibility repair — 2026-09-08

## Status

IMPLEMENTED / CI PASS / LIVE SMOKE PASS. FULL P1.2 COMPACTION/RECOVERY STILL PENDING.

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
- `tools/codex_large_context_live.py`
- `tests/test_codex_large_context_live.py`

`app/api/routes.py` installs the compatibility layer after existing V2 runtime hardening so it wraps the final Codex streaming path.

The layer covers both the V2 browser/tool stream and the legacy minimal Codex Responses stream.

Regression coverage verifies:

1. heartbeat is a real `response.in_progress` SSE event rather than a comment;
2. zero/missing usage is replaced with positive conservative accounting;
3. continuation usage grows through `previous_response_id`;
4. real non-zero usage is never overwritten;
5. unrelated non-terminal Responses events are unchanged;
6. a non-zero Codex turn preserves its already-written private JSONL observation so the outer live runner can still harvest that turn's UWA log delta before classifying the failure.

## CI

Stream compatibility implementation head:

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

Failed-turn evidence wrapper head:

```text
0c14742fbd3b4b6655a17f18e457f3c3caefcd7c
```

Security hardening workflow:

```text
run #313
id 34154114366
status completed
conclusion success
```

Both runs cover the macOS/Ubuntu security matrix, reproducible upstream regression suite and public-repository-safety gate.

## Acceptance instrumentation gap: CLOSED

The original P1.2 runner raised immediately when a Codex turn exited non-zero, so the outer loop could not harvest the UWA log delta for that failed turn. `tools/codex_large_context_live.py` now preserves the already-written private JSONL observation and lets the unchanged outer protocol scan that turn's UWA log delta before the ACK/contract check fails.

This changes evidence harvesting only; it does not weaken or alter P1.2 PASS criteria.

## Real macOS live smoke: PASS

After replacing the UWA listener so the repaired code was definitely active, a short Codex completion produced exact output and non-zero usage:

```text
LISTENER_REPLACED=YES
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
CODEX_RC=0
REPLY_EXACT=YES
INPUT_TOKENS=7113
OUTPUT_TOKENS=54
NONZERO_USAGE=YES
ERROR_COUNT=0
USAGE_SMOKE_PASS=YES
CODEX_USAGE_MARKERS=1
P1_STREAM_USAGE_SMOKE_PASS
```

The newly appended UWA log contained exactly one numeric-only `[CODEX_USAGE]` marker with the same estimate. The previous live blocker where Codex saw zero usage on every completion is therefore closed.

Detailed smoke record: `docs/CODEX_P1_STREAM_USAGE_LIVE_SMOKE_2026-09-08.md`.

## Current live gate

The next action is now the full P1.2 same-thread large-context run via:

```bash
python3 tools/codex_large_context_live.py run
```

The run must still prove all of the following before P1.2 can close:

1. same-thread context growth survives long browser-backed turns;
2. native Codex actually invokes `/v1/responses/compact` and UWA returns a successful compact result;
3. the conversation-only token survives compaction without being restated;
4. the final turn uses a real local tool to write/read exact result bytes;
5. the independent checker returns PASS.

P1.2 remains open until those real macOS criteria are satisfied.
