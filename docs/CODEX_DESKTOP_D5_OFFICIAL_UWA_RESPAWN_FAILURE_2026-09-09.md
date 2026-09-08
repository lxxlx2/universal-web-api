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

## Leading diagnosis

`tools/codex_provider_switch.py` currently contains a separate `stop_uwa_listener()` implementation. It verifies listener ownership and stops the listening process, but it does not perform the launcher/supervisor cleanup used by the hardened lifecycle manager.

`tools/codex_uwa_lifecycle.py` has the stronger authoritative stop path. It discovers owned launcher candidates from the private pidfile and process ancestry, stops launchers before listeners, requires the port to become empty, escalates fail-closed when required, and removes the stale pidfile.

The live symptom is consistent with the weaker provider-switch stop terminating the current listener while an owned launcher/supervisor survives and recreates a new listener.

This is a leading diagnosis pending local process-parent evidence. The repair should converge official switching on the versioned lifecycle stop implementation rather than maintaining two independent stop semantics.

## Release impact

```text
Desktop D1    PASS / CLOSED
Desktop D2    PASS / CLOSED
Desktop D3    PASS / CLOSED
Desktop D4    PASS / CLOSED
Desktop D5    BLOCKED / CURRENT
```

Do not run the harmless official-route request yet. First collect metadata-only process ancestry evidence, fix the lifecycle duplication, run focused regression tests, and repeat the D5 official restore from a known UWA state.

No account identifiers, usage amounts, private prompts, thread ids, browser ids, raw PIDs, cookies, credentials, or private trace contents are recorded here.
