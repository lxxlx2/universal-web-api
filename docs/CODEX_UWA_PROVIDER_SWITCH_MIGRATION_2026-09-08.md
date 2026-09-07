# Versioned UWA provider switch migration — 2026-09-08

## Status

IMPLEMENTED / LIVE VALIDATION PENDING.

The last executable dependency in the normal UWA entry path was a private local helper:

```text
~/.uwa/config_switch.py uwa
```

The helper contract was inspected on the macOS acceptance machine and migrated into repository-tracked tooling.

## Migrated UWA contract

`tools/codex_provider_switch.py uwa` now manages the Codex-side bridge configuration.

UWA mode sets these top-level values:

```toml
model = "chatgpt"
model_provider = "uwa"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
```

It also owns the exact `[model_providers.uwa]` table:

```toml
[model_providers.uwa]
name = "Universal Web API"
base_url = "http://127.0.0.1:8199/v1"
wire_api = "responses"
requires_openai_auth = false
supports_websockets = false
request_max_retries = 0
stream_max_retries = 0
stream_idle_timeout_ms = 300000
```

Model-specific top-level overrides that should not leak from normal account mode into the UWA `chatgpt` compatibility model are temporarily removed while UWA is active:

```text
model_context_window
model_auto_compact_token_limit
model_catalog_json
```

The legacy helper also treated `approval_policy` and `sandbox_mode` as UWA-owned values. The versioned implementation preserves the pre-UWA values of these non-model settings in a private restore-state file and restores them when returning to official mode.

The official-mode contract remains intentionally different for model selection: it does not restore top-level `model`, `model_provider`, or `model_reasoning_effort` pins, so the signed-in account/workspace model picker remains authoritative.

## Preservation rule

The versioned switch parses/validates TOML and preserves unrelated Codex configuration such as Desktop settings, plugins, MCP servers, project trust settings, hooks, features, shell policy and unrelated model providers.

Only the explicit UWA-managed root values and the `[model_providers.uwa]` table are rewritten.

Before a real mutation, a timestamped private config backup is created outside the public repository.

## Restore state

The repository code may write private state under:

```text
~/.uwa/codex-provider-restore.json
```

This file contains only the small set of UWA-temporarily-overridden top-level settings required for exact restoration. It is not committed.

For one-time migration from an already-active legacy UWA configuration, the code may read the old private `~/.uwa/config.official.toml` snapshot only to seed those restore-only fields when no new restore state exists. Normal operation no longer depends on that legacy file.

## Wrapper migration

`tools/install_codex_uwa_commands.py` now installs a `codex-uwa` thin wrapper that calls:

```text
codex_uwa_memory_guard.py disable
codex_provider_switch.py uwa
codex_uwa_lifecycle.py restart
```

The wrapper no longer references or executes `~/.uwa/config_switch.py`.

## Regression coverage

Focused regression coverage now checks:

- exact UWA root/provider contract;
- preservation of unrelated Desktop/plugin/provider configuration;
- removal of UWA-incompatible model-specific overrides while active;
- private restore-state creation with restrictive permissions;
- restoration of pre-UWA approval/sandbox/context/catalog values;
- official mode still removes model/provider/reasoning pins;
- installed wrappers contain no `config_switch.py` dependency.

Implementation commits culminate at:

```text
3eed07309ea2d6c64957d541bb8cbb690ea020ed
```

Security hardening CI #289 is the implementation CI. At the time this checkpoint was written, platform security and public-repository-safety jobs had passed while the reproducible upstream regression job was still running.

## Live gate

Before this migration is marked PASS, the real macOS acceptance machine must prove:

1. focused provider/wrapper tests pass from the pulled branch;
2. installed `~/bin/codex-uwa` contains no reference to the private helper;
3. `codex_provider_switch.py uwa` succeeds on the real existing Codex configuration;
4. unrelated TOML configuration remains semantically unchanged;
5. `codex-uwa` completes a real versioned restart and health check;
6. provider status reports UWA after restart.

Only after this live gate passes is the final Git-external executable dependency considered closed and P1.2 large-context work begins.
