# P1.2 native remote V2 precondition live — PASS — 2026-09-08

## Classification

The UWA provider precondition gate is **PASS**.

Observed live evidence:

```text
UWA_MODE_CHANGED=YES
model_provider="uwa"
model="chatgpt"
model_reasoning_effort="high"
UWA_RESTORE_STATE=UPDATED

CODEX_UWA_MEMORIES_DISABLED
generate_memories=false
use_memories=false

MODEL_PROVIDER_UWA=YES
MODEL_CHATGPT=YES
REASONING_HIGH=YES
APPROVAL_ON_REQUEST=YES
SANDBOX_WORKSPACE_WRITE=YES
PROVIDER_NAME_BASELINE=YES
LOOPBACK_BASE_URL=YES
WIRE_API_RESPONSES=YES
OPENAI_AUTH_DISABLED=YES
WEBSOCKETS_DISABLED=YES
UWA_PROVIDER_CONTRACT_PASS=YES

SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES

UWA_REMOTE_V2_PRECONDITION_PASS
```

## Meaning

The previous invalid attempt was caused by running the remote-compaction compatibility helper while Codex was not in the managed UWA provider mode. That blocker is now cleared.

The versioned provider switch restored the exact managed UWA root/provider contract, disabled Codex Memories for the acceptance run, and preserved the expected loopback Responses transport and disabled OpenAI auth.

The UWA listener remained healthy and connected to the logged-in browser session.

## Current gate

The next valid step is the real native remote-compaction probe:

1. enable the fail-closed Codex 0.153.4 remote-compaction capability shim;
2. verify that only `[model_providers.uwa].name` changes from `Universal Web API` to `Azure`;
3. launch a fresh Codex CLI process through the dedicated remote-V2 small-step trigger probe;
4. require remote route/success evidence plus Codex rollout compaction lifecycle evidence.

Required success evidence remains:

```text
THRESHOLD_CROSSED=YES
PRE_TRIGGER_OVER_HARD_CAP=NO
ROLLOUT_COMPACT_MARKER_DELTA>=1
REMOTE_COMPACT_ROUTE_DELTA>=1
REMOTE_COMPACT_SUCCESS_DELTA>=1
AUTO_COMPACT_MODE=REMOTE
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

## Gate status

```text
P1.2 remote V2 implementation/CI              PASS
P1.2 UWA provider precondition live           PASS
P1.2 native remote compact macOS live         CURRENT
P1.2 same-thread post-remote recovery         pending
```
