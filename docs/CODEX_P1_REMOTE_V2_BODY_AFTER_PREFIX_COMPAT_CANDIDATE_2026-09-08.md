# P1.2 BodyAfterPrefix compatibility candidate — 2026-09-08

## Source finding

Codex 0.153.x supports `model_auto_compact_token_limit_scope` with two values:

- `total` — default; count the full active context against the auto-compaction limit.
- `body_after_prefix` — count growth after the carried compaction-window prefix while still enforcing the independent full context-window hard cap.

The post-compact recovery diagnostics show compaction reducing active history to roughly 40k-43k tokens, followed by a rebound to roughly 58k before the next useful recovery stage. This is consistent with fixed model-visible prefix/tool-schema overhead being charged again under the default `total` scope.

## UWA integration observation

`tools/codex_provider_switch.py` currently manages UWA-only restore state for `model_context_window`, `model_auto_compact_token_limit`, and `model_catalog_json`, but does not manage `model_auto_compact_token_limit_scope`.

## Candidate fix

For UWA mode only, manage:

```toml
model_auto_compact_token_limit_scope = "body_after_prefix"
```

The switch must capture and restore any pre-existing user value when returning to official mode. This should avoid repeated compaction caused by carried fixed-prefix overhead without falsifying provider usage or increasing the advertised context window.

This is a candidate until the live user's current config value is verified and focused regression tests are added.

No private thread id, rollout path, prompt body, token value, local PID, or account data is recorded here.
