# P1.2 Remote V2 post-compact token rebound — 2026-09-08

## Live checkpoint

Read-only rollout diagnostics on the existing private P1.2 thread showed six compaction markers.

Observed per-compaction token state:

- compact 1: pre 57674 -> post 39719
- compact 2: pre 57877 -> post 40324
- compact 3: pre 58347 -> post 42979
- compact 4: pre 58636 -> post 43260
- compact 5: pre 58636 -> post 43260
- compact 6: pre 58636 -> post 40521

The latest recorded token usage then rebounded to 58933.

## Interpretation

The earlier retention-budget collision hypothesis is rejected as the direct cause of immediate re-compaction: every observed post-compaction token count is materially below both the native 57600 auto-compaction trigger demonstrated by the live probe and the 60800 hard cap.

The remaining blocker is a post-compact token rebound of roughly 15k-18k tokens before the next normal sampling/tool stage. That rebound repeatedly returns the thread to the auto-compaction region.

The diagnostic field `OBSERVED_CONTEXT_WINDOW=60800` came from rollout metadata and must not be treated as the provider catalog context window. The established live contract remains provider context window 64000, native auto-compaction trigger 57600, and hard cap 60800.

## Next investigation

Compare Codex `recompute_token_usage` with pre-turn context accounting, including base instructions, tool schemas and fixed context injected after compaction. Do not change the model catalog threshold until the rebound source is measured.

No private thread id, rollout path, token value, prompt body, command body, local PID, or account data is recorded here.
