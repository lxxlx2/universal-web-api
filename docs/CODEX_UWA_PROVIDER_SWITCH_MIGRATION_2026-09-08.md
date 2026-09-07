# Versioned UWA provider switch migration — 2026-09-08

## Status

PASS — implementation CI and real macOS live validation are complete.

The last executable dependency in the normal UWA entry path was a private local helper:

```text
~/.uwa/config_switch.py uwa
```

The helper contract was inspected on the macOS acceptance machine and migrated into repository-tracked tooling. Normal UWA startup no longer references or executes that helper.

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

`tools/install_codex_uwa_commands.py` installs a `codex-uwa` thin wrapper that calls:

```text
codex_uwa_memory_guard.py disable
codex_provider_switch.py uwa
codex_uwa_lifecycle.py restart
```

The wrapper no longer references or executes `~/.uwa/config_switch.py`.

## Regression coverage and CI

Focused regression coverage checks:

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

Security hardening CI #289 completed successfully, including upstream regression, macOS/Ubuntu security tests and public-repository-safety.

## Real macOS live evidence

The acceptance machine pulled the versioned implementation, installed the latest wrappers and validated the real existing Codex configuration.

Observed results:

```text
PRIVATE_HELPER_REFERENCE=NO
UWA_MODE_CHANGED=YES
UWA_RESTORE_STATE=UPDATED
UNRELATED_CONFIG_PRESERVED=YES
UWA_ROOT_CONTRACT=PASS
UWA_PROVIDER_CONTRACT=PASS
MODEL_SPECIFIC_OVERRIDES_CLEARED=YES
RESTORE_STATE=PRESENT
OLD_PID=67555
NEW_PID=29522
LISTENER_REPLACED=YES
HEALTH=PASS
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
model="chatgpt"
model_provider="uwa"
model_reasoning_effort="high"
UWA_RESTORE_STATE=PRESENT
VERSIONED_PROVIDER_SWITCH_LIVE_PASS
```

The local focused pytest command in that operator script did **not** run because the checked-out venv did not contain pytest:

```text
/Users/jerson/universal-web-api/venv/bin/python: No module named pytest
```

The following unconditional `echo FOCUSED_TESTS=PASS` was therefore a harness-command false positive and is not counted as local test evidence. This does not invalidate the gate because the same provider/wrapper regression suite was already covered by successful CI #289, while the real macOS switch/restart/health semantics were independently exercised live.

## Conclusion

The final known Git-external executable dependency in the normal UWA entry path is closed. `~/.uwa/config_switch.py` may remain on disk as legacy private state, but versioned operation does not depend on it.

Current development gate moves to P1.2 native Codex large-context compaction / stress / recovery.
