# Pre-D1 Desktop official-quota event — 2026-09-08

## Classification correction

This event happened **before the user executed any D1 preparation or result-collection commands**. It must therefore not be classified as a D1 live attempt or a D1 failure.

At the time of the event:

- an already-existing Desktop Codex conversation titled `Fix and harden V2 cargo flow` was open;
- the Desktop UI showed the official GPT-6 Astra model with Ultra reasoning before the resumed task;
- the user's five-hour official Codex/Work allowance had just refreshed;
- the user resumed the previously interrupted task in that existing conversation;
- the task consumed the refreshed official five-hour allowance and eventually showed the official usage-limit banner;
- the separate D1 commands that prepare `~/uwa-codex-acceptance` had not yet been run.

No account identifiers, exact usage amounts, local PIDs, thread IDs, or private project contents are recorded here.

## What this proves

The resumed existing Desktop conversation was on the official Codex/Work accounting path for at least the quota-consuming task. A UWA-backed turn would not consume the signed-in account's official Codex/Work five-hour allowance.

This does **not** prove that the planned fresh-thread D1 route is wrong, because D1 had not started.

## Model/routing interpretation

The strongest current interpretation is:

1. the existing conversation/active task retained its official Astra + Ultra selection and consumed official allowance;
2. the local Codex config had already been changed earlier to the managed UWA provider for future Codex sessions/turns;
3. after the official task ended or the Desktop surface refreshed/reconstructed its local session state, the UI could then pick up the UWA-managed provider/model alias instead of the old conversation's official model selection.

This is a hypothesis until local metadata confirms the model/provider boundary. Reaching a Codex usage limit by itself is not evidence of an automatic model switch.

## Current gate status

```text
M3 Desktop UI D1-D5       CURRENT
D1 fresh-thread UWA gate  NOT STARTED
pre-D1 official task      official quota consumed / route known to be official
```

Before D1 starts, use a tiny fresh-thread route probe and metadata-only evidence so a long Desktop task is never allowed to consume official quota accidentally.
