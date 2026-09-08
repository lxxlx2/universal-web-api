# Versioned UWA lifecycle live acceptance — 2026-09-07

## Result

PASS.

The repository-managed lifecycle implementation and thin `~/bin/codex-uwa*` wrappers were installed and exercised on the real macOS acceptance machine.

## Before

```text
OLD_PID=<old-listener>
OLD_CWD=<verified-repository-checkout>
```

The listener was the verified UWA checkout.

## Versioned stop

```text
STOPPED_LISTENERS=<old-listener>
PORT_EMPTY=YES
PORT_8199_EMPTY=YES
```

This closes the old failure mode where `codex-uwa-stop` printed success after TERM without proving that TCP 8199 was actually empty.

## Versioned start

```text
CODEX_UWA_MEMORIES_DISABLED
generate_memories=false
use_memories=false
OLD_LISTENER_PIDS=NONE
NEW_LISTENER_PIDS=<different-new-listener>
LISTENER_REPLACED=YES
HEALTH=PASS
```

The installed `codex-uwa` wrapper delegated to the repository lifecycle tool and did not reuse the previous healthy listener.

## Independent post-start verification

```text
OLD_PID=<old-listener>
NEW_PID=<different-new-listener>
LISTENER_REPLACED=YES
NEW_CWD=<verified-repository-checkout>
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
VERSIONED_LIFECYCLE_PASS
```

## Conclusion

The stale-runtime lifecycle blocker is closed.

The versioned lifecycle now proves all of the following on macOS:

1. actual TCP 8199 listener discovery;
2. listener cwd ownership validation;
3. stop success only after the port is empty;
4. restart uses a different listener PID rather than reusing a healthy stale process;
5. the new listener belongs to the expected checkout;
6. UWA `/health` is healthy and the controlled browser is connected;
7. UWA mode automatically disables Codex Memories;
8. the user-facing `~/bin` commands are thin wrappers whose lifecycle behavior comes from the current Git checkout.

## Historical note

At the time of this acceptance, `~/bin/codex-uwa` still called a private local provider-config helper. That dependency was subsequently migrated into repository-tracked `tools/codex_provider_switch.py`; normal operation no longer depends on the private helper.

Live process identifiers are intentionally redacted in the public record. The acceptance result depends on replacement/ownership/health semantics, not on publishing machine-local PIDs.
