# P1.2 UWA Auto-Compact Scope Live Check — 2026-09-08

Live local Codex configuration inspection confirmed that the UWA profile currently has no explicit `model_auto_compact_token_limit_scope`, `model_auto_compact_token_limit`, or `model_context_window` top-level override.

Observed safe state:

- `model_auto_compact_token_limit_scope`: absent
- effective scope therefore uses Codex default `total`
- `model_auto_compact_token_limit`: absent
- `model_context_window`: absent

This aligns with the current post-compaction token rebound diagnosis: UWA mode is using Codex's default full-active-context accounting rather than `body_after_prefix` accounting for the carried compaction-window prefix.

Planned compatibility change: UWA provider switch should manage `model_auto_compact_token_limit_scope = "body_after_prefix"` as a UWA-only override and include the key in private restore state so official mode restores the user's prior value or removes the UWA-injected value.

No credentials, thread IDs, prompts, local paths, process IDs, or private trace contents are recorded here.
