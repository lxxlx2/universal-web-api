# P1.2 remote compaction capability audit — 2026-09-08

## Scope

Determine the narrowest safe way for the normal UWA custom Codex provider to select native remote Responses compaction on the installed Codex CLI `0.153.4`, without enabling unrelated OpenAI-specific behavior.

Upstream exact-release source inspected at tag/commit:

```text
rust-v0.153.4
3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

## Exact capability classifier

For configured providers, Codex 0.153.4 exposes remote compaction V2 only when:

```text
provider.is_openai()
OR
is_azure_responses_provider(provider.name, provider.base_url)
```

Otherwise remote compaction is `Unsupported` and native auto-compaction uses the local fallback.

The current UWA provider is intentionally not OpenAI-authenticated and has a local loopback base URL, so its existing friendly name `Universal Web API` leaves remote compaction unsupported.

## Why not rename to OpenAI

`ModelProviderInfo::is_openai()` is an exact name test against `OpenAI`. That predicate is also used by broader Codex/OpenAI backend behavior and extension routing. Renaming UWA to `OpenAI` would therefore enable more than remote compaction and is rejected.

## Azure detector impact

The exact Azure detector returns true when either:

1. provider name equals `azure` case-insensitively; or
2. the base URL contains an Azure-specific marker.

Changing the actual UWA loopback URL to imitate an Azure hostname would alter transport/DNS and is unnecessary.

Using only:

```toml
[model_providers.uwa]
name = "Azure"
```

while preserving every other UWA provider field is narrower.

Exact-release behavior established:

```text
provider id                         remains `uwa`
base_url                            remains http://127.0.0.1:8199/v1
wire_api                            remains responses
requires_openai_auth                remains false
supports_websockets                 remains false
is_openai()                         false
supports_codex_backend_routes()     false
remote_compaction                   V2
```

`ConfiguredModelProvider::models_manager()` continues to build the normal provider-backed models endpoint from the same `ModelProviderInfo`; the Azure name does not replace the configured loopback URL.

## Remote compact request path

The Codex 0.153.4 remote V2 compaction flow uses the existing turn/provider client and compaction request kind. The compact endpoint is the provider-relative Responses endpoint:

```text
responses/compact
```

Therefore the UWA target remains:

```text
http://127.0.0.1:8199/v1/responses/compact
```

No Azure-specific URL, auth, or alternate request body is selected merely because the capability detector matched the provider name.

## Known side effect

The same Azure detector is used by `codex doctor` when deciding whether to probe the `/models` route. With the compatibility name `Azure`, `codex doctor` skips its own models-route reachability probe.

This does not disable the normal runtime provider models manager. The project already has direct UWA model-catalog health checks and live Codex model-catalog acceptance. The doctor behavior is a deliberate compatibility tradeoff and remains documented here.

## Decision

For Codex `0.153.4`, adopt the narrow compatibility shim:

```toml
[model_providers.uwa]
name = "Azure"
base_url = "http://127.0.0.1:8199/v1"
wire_api = "responses"
requires_openai_auth = false
```

All other existing provider fields remain unchanged.

## Versioned implementation

A fail-closed helper is tracked at:

```text
tools/codex_remote_compaction_compat.py
```

Regression coverage:

```text
tests/test_codex_remote_compaction_compat.py
```

The helper refuses to modify the config unless all of these are true:

```text
top-level model_provider       uwa
provider table                 model_providers.uwa
provider name                  Universal Web API or Azure
base_url                       http://127.0.0.1:8199/v1
wire_api                       responses
requires_openai_auth           false
supports_websockets            false
```

When enabled, it changes only the managed provider's `name` field to `Azure`, creates a local backup, and leaves model selection, auth, base URL, retry policy, browser state, all unrelated config and all other provider tables untouched.

Security hardening #351 / run `34164070091` at head `127ed09fbb1f8941ff4332db72bf498fb9f80287` completed with `success`. The implementation/CI gate is therefore closed PASS.

## Current live gate

Run the compatibility helper against the real managed UWA config, verify the exact safe contract, then rerun the small-step native threshold probe.

Required remote evidence:

```text
threshold crossed safely
REMOTE_COMPACT_ROUTE_DELTA >= 1
REMOTE_COMPACT_SUCCESS_DELTA >= 1
AUTO_COMPACT_MODE=REMOTE
ROLLOUT_COMPACT_MARKER_DELTA >= 1
```

That proves native Codex selected the remote compact endpoint. It still does not by itself close all of P1.2: same-thread post-compact recovery of the original conversation-only synthetic token through a real local write/read remains mandatory afterward.

Do not mark P1.2 closed from a direct compact HTTP probe alone; P1.1 already proves that endpoint. P1.2 requires native Codex auto-compaction to select the remote endpoint and preserve conversation recovery.
