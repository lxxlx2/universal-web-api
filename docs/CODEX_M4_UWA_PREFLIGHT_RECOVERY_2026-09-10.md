# Codex M4 UWA Preflight Recovery — 2026-09-10

## Status

M4 remains CURRENT. The first real-project pilot invocation stopped before any Codex coding turn because the configured route was still `uwa / chatgpt / high` but the local UWA health endpoint was unavailable to the runner.

Observed safe metadata:

```text
project branch                         codex-web-bridge-v2
project worktree dirty count           0
configured provider/model/effort       uwa / chatgpt / high
health running count                   unavailable
health browser connected               unavailable
pilot result                           FAIL before agent turn
failure class                          uwa_health_precondition_failed
```

No project implementation file was modified and no real-project Codex task started in this failed invocation.

## Repair

`tools/codex_m4_real_project_pilot_safe.py` now performs a fail-closed lifecycle preflight before entering the M4 runner.

Behavior:

```text
health ready + running=0
→ continue without lifecycle mutation

health unavailable and no listener
→ start UWA through the versioned lifecycle manager
→ wait for healthy browser-connected running=0 state
→ continue M4

owned listener present but unhealthy
→ restart through the versioned lifecycle manager
→ wait for healthy browser-connected running=0 state
→ continue M4

healthy service with active work
→ do not restart it
→ leave the base M4 precondition to fail closed

foreign listener
→ lifecycle ownership check refuses to touch it
```

The wrapper suppresses raw lifecycle PID details from its normal acceptance output. The existing lifecycle manager remains authoritative for listener ownership and health.

Repair commit: `31f4231`.

## Next action

Pull the active branch and rerun the same one-shot M4 safe runner. A successful rerun must still satisfy every original M4 coding, test, route, cleanup and guarded Git acceptance requirement.
