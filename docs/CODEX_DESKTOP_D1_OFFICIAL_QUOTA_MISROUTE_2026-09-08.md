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

## Local metadata confirmation

A local metadata-only inspection of recent Codex JSONL records confirmed the provider/model boundary directly:

```text
2026-09-08 22:07:52  model=gpt-6-astra  provider=openai  effort=ultra
2026-09-08 22:07:48  model=gpt-6-astra  provider=openai  effort=ultra
2026-09-08 22:07:48  model=gpt-6-astra  provider=openai  effort=ultra
2026-09-08 17:30:23  model=chatgpt      provider=uwa     effort=high
2026-09-08 14:54:18  model=chatgpt      provider=uwa     effort=high
```

One 22:07 JSONL contained multiple historical `reasoning_effort` values (`low,medium,ultra,xhigh`) in its metadata, but its active model/provider identity remained `gpt-6-astra` / `openai` and its top-level effort was `ultra`. The exact JSONL paths and thread identifiers remain private.

## What this proves

The resumed existing Desktop task at 22:07 ran through the official OpenAI Codex provider using GPT-6 Astra with Ultra reasoning. The earlier 17:30 and 14:54 Codex sessions were UWA-backed (`model=chatgpt`, `provider=uwa`, `effort=high`).

Therefore the quota-consuming resumed task did **not** automatically fall back to UWA after the official allowance refreshed or was later exhausted. The model/provider identities are distinct in local metadata.

This still does **not** prove that the planned fresh-thread D1 route is wrong, because D1 had not started.

## Routing interpretation

The supported interpretation is now:

1. the existing Desktop conversation/task retained or recreated an official `openai` / `gpt-6-astra` / `ultra` execution state when resumed;
2. UWA-backed sessions existed separately earlier in the day and were recorded as `provider=uwa` / `model=chatgpt` / `effort=high`;
3. the local `~/.codex/config.toml` UWA override is therefore not sufficient evidence that an already-existing Desktop conversation will be converted in place to UWA;
4. reaching the official Codex usage limit is not evidence of an automatic Astra -> UWA switch.

The exact mechanism by which Desktop chooses provider state for an existing conversation still requires route-specific testing. The leading hypothesis is that an existing Desktop conversation carries or reconstructs its own official provider/model state independently of the current top-level local override.

## Current gate status

```text
M3 Desktop UI D1-D5       CURRENT
D1 fresh-thread UWA gate  NOT STARTED
pre-D1 official task      openai / gpt-6-astra / ultra CONFIRMED
prior UWA sessions        uwa / chatgpt / high CONFIRMED
```

Before D1 starts, use a tiny fresh-thread route probe and metadata-only evidence so a long Desktop task is never allowed to consume official quota accidentally.
