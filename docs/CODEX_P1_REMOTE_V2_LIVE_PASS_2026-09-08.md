# P1.2 native remote V2 compaction live — PASS — 2026-09-08

## Result

PASS.

Real macOS / Codex CLI 0.153.4 completed the native remote-compaction trigger path through the managed UWA provider and the narrow Azure-name capability shim.

## Preconditions

The managed UWA contract was active before the probe:

```text
model_provider="uwa"
model="chatgpt"
model_reasoning_effort="high"
UWA provider name="Azure"   # capability identity only
base_url=http://127.0.0.1:8199/v1
wire_api=responses
requires_openai_auth=false
supports_websockets=false
request_max_retries=0
stream_max_retries=0
stream_idle_timeout_ms=300000
SERVICE=healthy
BROWSER_CONNECTED=True
```

The capability helper changed only the provider display name from `Universal Web API` to `Azure`; the provider id, loopback endpoint, Responses transport, auth behavior, retry behavior and unrelated Codex configuration remained unchanged.

## Live threshold evidence

The dedicated small-step probe approached the native Codex 0.153.4 auto-compaction threshold without crossing the hard context cap:

```text
AUTO_COMPACT_LIMIT=57600
HARD_CONTEXT_LIMIT=60800

PHASE=FINE ROUND=09 ACTIVE_LAST_TOKENS=56812 MARGIN_TO_AUTO=788
PHASE=FINE ROUND=10 ACTIVE_LAST_TOKENS=57674 MARGIN_TO_AUTO=-74

THRESHOLD_CROSSED=YES
PRE_TRIGGER_ACTIVE_TOKENS=57674
PRE_TRIGGER_OVER_HARD_CAP=NO
PRE_TRIGGER_ROLLOUT_COMPACT_MARKERS=0
```

## Native remote V2 evidence

The following trigger turn then succeeded:

```text
TRIGGER_REPLY_EXACT=YES
TRIGGER_TOOL_EFFECTS=0
ROLLOUT_COMPACT_MARKER_DELTA=1
REMOTE_COMPACT_ROUTE_DELTA=1
REMOTE_COMPACT_SUCCESS_DELTA=1
TOKEN_LEAK_WORKSPACE=NO
AUTO_COMPACT_MODE=REMOTE
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

This proves all of the following on the real acceptance machine:

1. Codex persisted/restored the active context token state correctly;
2. the 57,600 auto-compaction threshold was reached before the 60,800 hard cap;
3. Codex selected remote compaction rather than local fallback;
4. the request reached the UWA remote-V2 ordinary Responses path;
5. UWA successfully produced the required remote V2 `type=compaction` result;
6. Codex accepted the result and recorded a compaction lifecycle marker;
7. the synthetic conversation-only token did not leak into the workspace during the trigger probe.

## Remaining P1.2 gate

P1.2 is not closed yet. One separate recovery gate remains:

```text
remote V2 compact
→ continue the same Codex thread
→ do not search local rollout/session/history/private UWA stores
→ recover the original conversation-only synthetic token from compacted model-visible context
→ perform a real local write/read through Codex
→ exact checker PASS
```

After that passes, P1.2 can close and the accelerated merge-blocking sequence moves to the minimal P1.3 continuity/restart blockers, Desktop UI D1-D5, one real-project pilot, final regression/safety/docs and merge-to-main.
