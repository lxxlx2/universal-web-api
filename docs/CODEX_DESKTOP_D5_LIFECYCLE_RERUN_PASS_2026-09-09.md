# Codex Desktop D5 repaired lifecycle rerun PASS — 2026-09-09

## Result

The repaired D5 official-provider lifecycle rerun passed the shutdown and no-respawn portion of the live gate on macOS.

Starting from a healthy managed UWA state, the repaired official provider switch was executed. Metadata-only local checks then observed the managed repository state at T+0, T+3, T+10 and T+20 seconds.

At every observation point:

```text
repository-owned start.py count = 0
repository-owned main.py count = 0
TCP 8199 listener count = 0
private UWA pidfile present = NO
```

The versioned lifecycle status also reported:

```text
PORT=8199
LISTENER_PIDS=NONE
STATUS=STOPPED
```

The provider configuration independently reported account defaults:

```text
model=<default>
model_provider=<default>
model_reasoning_effort=<default>
model_auto_compact_token_limit_scope=<default>
UWA_RESTORE_STATE=ABSENT
```

The repository working tree remained clean.

## Conclusion

The confirmed D5 respawn defect is closed at the lifecycle level. The official switch now stops the managed launcher and listener strongly enough that `start.py` does not recreate `main.py`, the port remains empty, and the private pidfile remains absent through the observation window.

Desktop D5 is not yet fully closed because the final harmless official-provider request still needs to be executed when official Codex quota is available. That remaining task verifies a real post-restore official request, not the lifecycle shutdown behavior.

No raw process identifiers, account identifiers, usage amounts, browser identifiers, cookies, credentials, private prompts, or private traces are recorded here.
