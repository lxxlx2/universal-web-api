# Codex Web Bridge Progress

## Branches

- stable verified base: `security-hardening`
- active V2 development: `codex-web-bridge-v2`
- V2 Draft PR: #2

## Verified macOS milestones

```text
Stage A-F protocol/CLI acceptance           PASS
aggregate A-F checker                       PASS
Responses tool/call-id continuity           PASS
P1.1 Responses compact direct live          PASS
versioned lifecycle/provider switch CI/live PASS
P1.2 automated runner CI                    PASS
P1.2 stream compatibility CI #313           PASS
P1.2 non-zero usage macOS smoke             PASS
P1.2 rollout TokenCount persistence         PASS
P1.2 second full large-context live         FAIL / runner threshold defect identified
```

Stage E/F remain protocol/CLI evidence and do not close the mandatory Desktop D1-D5 gate.

## P1.2 live history

### Attempt 1

Seed plus seven filler continuations succeeded; round 8 failed with SSE idle timeout. Successful turns exposed all-zero Responses usage.

Repairs:

- parseable `response.in_progress` heartbeat;
- bounded fallback usage when real usage is absent/zero;
- failed-turn evidence harvesting.

CI #313 passed, followed by a real non-zero-usage macOS smoke.

### Attempt 2

The repaired full run reported CLI cumulative usage:

```text
21230 -> 42219 -> 70125 -> 104948 -> 146688 -> 195345 -> 250919
```

Rounds 1-7 returned exact filler ACKs with zero tool effects and zero remote compact counters. Round 8 failed the filler contract.

## Read-only catalog/config/rollout diagnosis

Live inspection established:

```text
Codex version                 0.153.4
cache client version          0.153.4
cache context window          64000
live context window           64000
explicit auto-compact field   null
persisted TokenCount events   9
TokenCount model window       60800
context override              none
auto-compact override         none
```

The real rollout preserved usage. Safe per-response active-context values reached:

```text
7213 -> 14130 -> 21047 -> 27964 -> 34881 -> 41798 -> 48715 -> 55632
```

## Exact Codex 0.153.4 source diagnosis

`rust-v0.153.4` resolves to upstream commit `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`.

Confirmed source facts:

1. Resume/fork restores the latest persisted `EventMsg::TokenCount`.
2. Normal `response.completed` usage is persisted and exposed through `TokenUsageInfo`.
3. `context_window_token_status()` uses `last_token_usage.total_tokens` plus post-model history as active-context usage, not lifetime cumulative usage.
4. `ModelInfo::auto_compact_token_limit()` derives 90% of the resolved context window when the explicit field is absent: `57,600` for the current 64K model.
5. The separate hard effective full-context cap is 95%: `60,800`.
6. Round 7 ended at `55,632`, only 1,968 tokens below auto-compact.
7. `run_turn()` performs pre-turn compaction before context updates and before the new user message are recorded; the exact source explicitly notes that pending incoming items are not yet estimated for this check.
8. The old runner then appended another 20KB filler after the check, jumping across the 57,600 trigger and toward the hard boundary inside round 8.

Therefore attempt 2 is now classified primarily as an acceptance-runner threshold-crossing defect, not proof of a broken Codex pre-turn compact trigger.

A separate capability fact remains: the custom UWA provider is `RemoteCompactionSupport::Unsupported`, so when auto-compaction genuinely triggers it should currently choose the local fallback path rather than `/v1/responses/compact`.

## Current gate

Use coarse filler until active context is close to 57,600, then ~2KB fine filler until one successful response lands only slightly above the auto-compact threshold. Send a tiny next-turn trigger and inspect bounded Codex rollout compact lifecycle evidence.

Expected split:

```text
small-step threshold crossed + next-turn local compact observed
    -> trigger path PASS; remote-capability shim becomes separate next gate

no compact after persisted active context is already >57600
    -> trigger/persistence mismatch remains
```

Detailed record: `docs/CODEX_P1_MODEL_CACHE_RESUME_DIAG_2026-09-08.md`.

## Current status

```text
P1.1 compact endpoint + live protocol             PASS
versioned lifecycle/provider switch               PASS
P1.2 stream/usage compatibility                    PASS
P1.2 TokenCount persistence                        PASS
P1.2 attempt-2 threshold diagnosis                 PASS
P1.2 small-step auto-compact trigger probe         CURRENT
P1.3 affinity/restart/uncertain-effect              pending
Desktop UI live gate D1-D5                         pending / mandatory
```

## Production-hardening roadmap

```text
P1.2 native Codex large-context compaction / stress / recovery
P1.3 lost-affinity / restart + identity fencing + uncertain-effect recovery
Desktop D1-D5 actual UI acceptance
P1.4 real-project long-task pilot
P2 per-continuation serialization / queue planes / controlled-tab stale-result hardening
P3 MCP/plugin namespace + capability fidelity + multi-agent/tool fan-out
P4 Responses SSE slimming + bounded trace/transcript hygiene
P5 runtime/build identity + compatibility preflight + final regression/release checklist
```

## Recording discipline

Every live result, failure, repair and disruptive checkpoint must be committed before the next step. README, canonical current state, this file, stage/failure records and Draft PR must stay aligned.

## Final merge plan

Merge `codex-web-bridge-v2` into `main` only after P1 hardening, actual Desktop UI acceptance, the real-project pilot, final regression, CI, documentation and repository-safety checks are green.
