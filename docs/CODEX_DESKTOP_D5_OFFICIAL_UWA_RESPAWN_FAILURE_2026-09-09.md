# Codex Desktop D5 official restore: UWA listener respawn failure — 2026-09-09

## Classification

Desktop D5 exposed a real lifecycle defect during the first official-account restore live run. The defect has since been repaired and the repaired lifecycle rerun has passed live. D5 still has one remaining post-restore official-request check before full closure.

The configuration/authentication side of the first official switch succeeded:

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

The first switch also reported that the then-current UWA listener had been stopped and that Desktop was reopened.

However, the immediate versioned lifecycle status then observed a fresh healthy listener on TCP 8199. Raw process identifiers are intentionally omitted from this public record.

```text
post-switch PORT=8199
post-switch LISTENER_PIDS=<replacement listener present>
post-switch STATUS=HEALTHY
```

That first run could not pass D5 because a clean official restore requires the managed UWA service to remain stopped after the switch.

## Confirmed root cause

Metadata-only process ancestry collected immediately after the failure confirmed the respawn mechanism:

```text
launchd
  -> repository-owned start.py launcher
       -> repository-owned main.py TCP 8199 listener

private ~/.uwa/uwa.pid -> start.py launcher
```

The replacement `main.py` listener was a child of the still-running repository `start.py` launcher. The launcher itself was detached under launchd, and the private UWA pidfile still referenced that launcher. This proved that the first official switch stopped only the then-current listening child while leaving the launcher alive, allowing it to recreate the listener.

Before the repair, `tools/codex_provider_switch.py` contained a separate listener-only `stop_uwa_listener()` implementation. It verified listener ownership and terminated the listening process, but it did not perform the launcher/supervisor cleanup already implemented by the hardened lifecycle manager.

`tools/codex_uwa_lifecycle.py` contains the authoritative stop path. It discovers owned launcher candidates from the private pidfile and process ancestry, stops launchers before listeners, requires the port to become empty, escalates fail-closed when required, and removes the stale pidfile.

## Implemented lifecycle repair

Commit `143b396` repairs the defect by making `tools/codex_provider_switch.py` reuse the authoritative launcher-aware `tools/codex_uwa_lifecycle.stop_uwa()` path.

The compatibility `stop_uwa_listener()` wrapper preserves the existing provider-switch return contract while reusing hardened lifecycle ownership validation, launcher-first termination, empty-port verification, escalation behavior, and pidfile cleanup.

Focused provider-switch and lifecycle regression coverage passes with 18 tests. The Security hardening GitHub Actions run for `143b396` also completed successfully.

## Repaired live rerun

The repaired official-provider lifecycle rerun passed the shutdown and no-respawn gate.

Metadata-only checks at T+0, T+3, T+10 and T+20 seconds all observed:

```text
repository-owned start.py count = 0
repository-owned main.py count = 0
TCP 8199 listener count = 0
private UWA pidfile present = NO
```

The versioned lifecycle status reported:

```text
PORT=8199
LISTENER_PIDS=NONE
STATUS=STOPPED
```

The provider status reported:

```text
model=<default>
model_provider=<default>
model_reasoning_effort=<default>
model_auto_compact_token_limit_scope=<default>
UWA_RESTORE_STATE=ABSENT
```

The repository working tree remained clean.

Detailed live evidence: `docs/CODEX_DESKTOP_D5_LIFECYCLE_RERUN_PASS_2026-09-09.md`.

## Release impact

```text
Desktop D1    PASS / CLOSED
Desktop D2    PASS / CLOSED
Desktop D3    PASS / CLOSED
Desktop D4    PASS / CLOSED
Desktop D5    LIFECYCLE PASS / final official request pending
```

The respawn defect is closed at the lifecycle level. The only remaining D5 item is a harmless real official-provider request after restore when official Codex quota is available. That remaining check verifies actual post-restore official execution and is separate from the now-passing shutdown behavior.

No account identifiers, usage amounts, private prompts, thread ids, browser ids, raw PIDs, cookies, credentials, or private trace contents are recorded here.
