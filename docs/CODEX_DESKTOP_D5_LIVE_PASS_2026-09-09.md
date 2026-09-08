# Codex Desktop D5 official restore and task — LIVE PASS — 2026-09-09

## Result

Desktop D5 is PASS / LIVE / CLOSED.

The gate required both a clean return from UWA mode to normal signed-in Codex account behavior and one harmless real Codex Desktop task through the restored official provider.

## Lifecycle restore evidence

The repaired provider-switch path had already passed the no-respawn rerun after commit `143b396`.

Metadata-only checks at T+0, T+3, T+10 and T+20 all observed:

```text
repository-owned start.py = 0
repository-owned main.py = 0
TCP 8199 listeners = 0
UWA pidfile present = NO
```

The versioned lifecycle helper reported `STATUS=STOPPED`. Provider status remained at signed-in account defaults and `UWA_RESTORE_STATE=ABSENT`.

## Harmless official-provider task

After official Codex allowance became available again, a fresh real Codex Desktop conversation was opened on the synthetic `uwa-hybrid-acceptance` workspace.

The Desktop model picker showed the signed-in account-controlled `GPT-6 Astra` option. The selected reasoning tier for this bounded task was Light. The task used real local Codex tools and appended exactly one synthetic local effect to `effects.log`.

Independent local checker result:

```text
OFFICIAL_EFFECT_COUNT=1
OFFICIAL_SOURCE_PASS
```

The working diff contained exactly one appended line:

```text
OFFICIAL_EFFECT_ONCE
```

Metadata-only route audit immediately after the task reported:

```text
configured provider/model/effort = account defaults
latest session provider = openai
latest session model = gpt-6-astra
latest session effort = low
UWA health = unavailable
post-marker UWA request count = 0
post-marker UWA response count = 0
route expectation for provider=openai = PASS
```

The intentionally stopped UWA service and zero post-marker UWA wire activity provide negative evidence that the successful task did not route through UWA.

## Classification

```text
D1 PASS / LIVE / CLOSED
D2 PASS / LIVE / CLOSED
D3 PASS / LIVE / CLOSED
D4 PASS / LIVE / CLOSED
D5 PASS / LIVE / CLOSED
Desktop gate PASS / LIVE / CLOSED
```

This closes the Desktop D1-D5 gate. The synthetic official workspace effect is intentionally left uncommitted so it can serve as the source state for the upcoming H3 official-to-UWA handoff acceptance.

No account identifiers, raw thread identifiers, raw process identifiers, browser identifiers, cookies, credentials, private prompts or private traces are recorded in this public evidence.
