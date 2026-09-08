# P1.2 UWA Body-After-Prefix Provider Switch — CI PASS — 2026-09-08

The UWA Codex provider switch now manages `model_auto_compact_token_limit_scope = "body_after_prefix"` as a UWA-only root override.

The private restore-state contract also manages this key so official mode restores an explicit pre-UWA value or removes the UWA-injected value when the original setting was absent. Existing restore-state files created before this key was managed are upgraded on the next UWA apply before the live config is overwritten; direct official restore with an older state does not delete an unmanaged scope.

Focused regression coverage includes:

- UWA replaces `total` with `body_after_prefix`;
- original explicit scope is captured and restored;
- original default/absent scope is restored by removing the UWA override;
- an already-active UWA config with an older restore-state file is upgraded safely;
- older state used directly for official restore does not authorize deletion of an unmanaged scope.

Security hardening CI run #466 completed successfully across public-repo-safety, Ubuntu Python 3.11/3.13, macOS Python 3.11/3.13, and the reproducible upstream regression job.

This change does not modify authentication, browser credentials, Responses/compaction wire protocol, model context-window advertisement, or UWA provider transport settings.
