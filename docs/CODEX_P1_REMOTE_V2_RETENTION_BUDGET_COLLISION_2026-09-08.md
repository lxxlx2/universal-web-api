# P1.2 remote-v2 retained-history budget collision — 2026-09-08

## Confirmed implementation facts

The current UWA Codex model catalog advertises:

- context window: 64,000 tokens
- truncation / auto-compaction limit: 57,600 tokens

Codex 0.153.4 remote-compaction V2 installs its replacement history by retaining selected recent messages under a fixed retained-message token budget of 64,000 tokens, then appending the compaction output and recomputing token usage.

Therefore the Codex retained-message budget alone is equal to UWA's entire advertised context window and greater than UWA's auto-compaction threshold.

## Live correlation

The P1.2 same-thread recovery produced no agent message and no tool call during the latest bounded attempt, while the rollout compaction marker count increased from 5 to 6. This is consistent with immediate post-compaction re-entry.

## Current hypothesis

The replacement history installed after remote V2 compaction remains above the 57,600-token auto-compaction limit, causing another auto-compaction before the recovery turn can reach ordinary model/tool execution.

## Next evidence gate

Before changing the model catalog, read only numeric rollout token-count metadata around compaction checkpoints and determine the actual post-compaction active token count. Use that measurement to choose the smallest safe model-catalog/context-window correction.

Do not change compaction response usage merely to mask the issue: Codex recomputes token usage after installing compacted history.

No private thread id, rollout path, prompt body, account data or synthetic token is recorded here.
