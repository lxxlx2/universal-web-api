# Codex Desktop D5 manual cleanup and official-quota block — 2026-09-09

## Result

After the first D5 official-account restore exposed a UWA listener respawn defect, the surviving managed launcher was stopped through the authoritative versioned lifecycle path.

Machine-observed non-sensitive evidence:

```text
PORT_EMPTY=YES
PORT=8199
LISTENER_PIDS=NONE
STATUS=STOPPED
UWA_PIDFILE=ABSENT
UWA_PYTHON_PROCESSES=NONE
model=<default>
model_provider=<default>
model_reasoning_effort=<default>
model_auto_compact_token_limit_scope=<default>
UWA_RESTORE_STATE=ABSENT
```

This confirms that `tools/codex_uwa_lifecycle.py stop` can cleanly terminate the managed launcher/listener set and remove the private pidfile while leaving Codex in account-default provider/model/reasoning configuration.

## Desktop state

Codex Desktop reopened in official-account mode and the model picker was again controlled by the signed-in account UI. The UI also showed that the official Codex/Work allowance was exhausted, so the harmless official-route live request could not be executed at this time.

A quota-limit state after a clean official restore is not classified as a bridge-routing failure. The harmless official task remains deferred until official allowance is available.

## Release impact

```text
D1 PASS / CLOSED
D2 PASS / CLOSED
D3 PASS / CLOSED
D4 PASS / CLOSED
D5 config/account-default restore evidence PASS
D5 managed-service cleanup evidence PASS via authoritative lifecycle stop
D5 provider-switch respawn defect REPAIR REQUIRED
D5 harmless official live request DEFERRED BY OFFICIAL QUOTA
D5 overall BLOCKED / CURRENT
```

The release-critical repair remains narrow: make `tools/codex_provider_switch.py official` reuse the authoritative launcher-aware lifecycle stop semantics, add regression coverage, rerun the clean restore, and perform the harmless official-route task once official quota is available.

No account identifiers, usage amounts, raw process IDs, private prompts, browser IDs, cookies, credentials, private trace contents or local pidfile contents are recorded here.
