# Codex P1 body-after-prefix live migration PASS — 2026-09-08

Live migration on the active UWA Codex configuration completed successfully.

Observed state:

- UWA provider mode remained active.
- `model_auto_compact_token_limit_scope` was set to `body_after_prefix`.
- remote compaction compatibility identity was re-enabled successfully (`UWA_PROVIDER_NAME=Azure`).
- private provider restore state exists.
- the restore-state entry for `model_auto_compact_token_limit_scope` exists and records that the pre-UWA configuration did not explicitly define the field.
- therefore switching back to official mode can remove the UWA-only override and restore Codex's original default `total` behavior.

Live acceptance marker:

`BODY_AFTER_PREFIX_MIGRATION_PASS=YES`

This closes the configuration-migration prerequisite for the next bounded same-thread post-remote-compaction recovery probe. It does not itself close P1.2 recovery; one live recovery pass is still required.
