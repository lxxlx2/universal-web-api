# Codex Desktop D5 official restore: UWA listener respawn failure — 2026-09-09

## Classification

Desktop D5 is BLOCKED by a real lifecycle defect discovered during the first official-account restore live run.

The configuration/authentication side of the official switch succeeded:

```text
OFFICIAL_MODE_CHANGED=YES
AUTH=UNCHANGED
MODEL_SELECTION=ACCOUNT_DEFAULT_UI
model=<default>
model_provider=<default>
model_reasoning_effort=<default>
model_auto_compact_token_limit_scope=<default>
UWA_RESTORE_STATE=ABSENT
```

The switch also reported that the then-current UWA listener had been stopped and that Desktop was reopened.

However, the immediate versioned lifecycle status then observed a fresh healthy listener on TCP 8199. Raw process identifiers are intentionally omitted from this public record.

```text
post-switch PORT=8199
post-switch LISTENER_PIDS=<replacement listener present>
post-switch STATUS=HEALTHY
```

Therefore D5 cannot be marked PASS. A clean official restore requires the managed UWA service to remain stopped after the switch.

## Confirmed root cause

Metadata-only process ancestry collected immediately after the failure confirmed the respawn mechanism:

```text
launchd
  -> repository-owned start.py launcher
       -> repository-owned main.py TCP 8199 listener

private ~/.uwa/uwa.pid -> start.py launcher
```

The replacement `main.py` listener was a child of the still-running repository `start.py` launcher. The launcher itself was detached under launchd, and the private UWA pidfile still referenced that launcher. This proves that the first official switch stopped only the then-current listening child while leaving the launcher alive, allowing it to recreate the listener.

`tools/codex_provider_switch.py` currently contains a separate `stop_uwa_listener()` implementation. It verifies listener ownership and terminates the listening process, but it does not perform the launcher/supervisor cleanup used by the hardened lifecycle manager.

`tools/codex_uwa_lifecycle.py` already contains the authoritative stop path. It discovers owned launcher candidates from the private pidfile and process ancestry, stops launchers before listeners, requires the port to become empty, escalates fail-closed when required, and removes the stale pidfile.

The release-critical repair is to make official switching reuse the versioned lifecycle stop implementation so provider switching and the installed `codex-uwa-stop` command have one stop contract.

## Release impact

```text
Desktop D1    PASS / CLOSED
Desktop D2    PASS / CLOSED
Desktop D3    PASS / CLOSED
Desktop D4    PASS / CLOSED
Desktop D5    BLOCKED / CURRENT
```

Do not run the harmless official-route request yet. First stop the surviving managed launcher through the versioned lifecycle path, fix the lifecycle duplication, run focused regression tests, and repeat the D5 official restore from a known UWA state.

No account identifiers, usage amounts, private prompts, thread ids, browser ids, raw PIDs, cookies, credentials, or private trace contents are recorded here.

## Implemented lifecycle repair checkpoint

The confirmed provider-switch lifecycle defect has been repaired in code.

`tools/codex_provider_switch.py` now delegates UWA shutdown to the authoritative launcher-aware `tools/codex_uwa_lifecycle.stop_uwa()` path instead of maintaining an independent listener-only shutdown implementation.

The compatibility `stop_uwa_listener()` wrapper preserves the existing provider-switch return contract while reusing hardened lifecycle ownership validation, launcher-first termination, empty-port verification, escalation behavior, and pidfile cleanup.

Focused provider-switch and lifecycle regression coverage passes with 18 tests.

Desktop D5 remains BLOCKED until the repaired live UWA-to-official restore is rerun successfully. The final harmless official-provider task remains pending while official Codex quota is unavailable.

