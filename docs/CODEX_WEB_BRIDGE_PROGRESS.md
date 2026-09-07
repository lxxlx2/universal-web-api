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
P1.2 second full large-context live         FAIL
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

The repaired full run reported:

```text
21230 -> 42219 -> 70125 -> 104948 -> 146688 -> 195345 -> 250919
```

Rounds 1-7 returned exact filler ACKs with zero tool effects and zero remote compact counters. Round 8 failed the filler contract.

## Read-only catalog/config diagnosis

Live inspection established:

```text
Codex version                 0.153.4
cache client version          0.153.4
cache context window          64000
live context window           64000
cache truncation limit        57600
live truncation limit         57600
context override              none
auto-compact override         none
visible compact lifecycle     none
```

So stale model cache, a larger effective catalog window, and explicit top-level overrides are closed hypotheses.

## Exact Codex 0.153.4 source diagnosis

`rust-v0.153.4` resolves to upstream commit `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`.

Confirmed source facts:

1. UWA's custom provider identity is `RemoteCompactionSupport::Unsupported`; remote compact is enabled only for recognized OpenAI/Azure providers.
2. Unsupported providers retain a local auto-compaction fallback.
3. Resume/fork already restores token state from the latest persisted `EventMsg::TokenCount`.
4. Normal `response.completed` handling records token usage, emits `TokenCount`, and ordinary events are persisted into rollout storage.

Therefore the earlier hypothesis that each fresh `codex exec resume` inherently loses token accounting is rejected.

## Current gate

The next read-only check is the actual P1.2 rollout. We need only bounded event-type and numeric token evidence:

```text
Does the rollout contain TokenCount events?
If yes, what are total/last token values and model_context_window?
Did an over-threshold TokenCount exist before a later resumed turn?
```

Do not print prompts, IDs, response bodies, tool payloads or the full rollout. Do not rerun the large-context test or change provider identity before this is known.

Detailed record: `docs/CODEX_P1_MODEL_CACHE_RESUME_DIAG_2026-09-08.md`.

## Current status

```text
P1.1 compact endpoint + live protocol             PASS
versioned lifecycle/provider switch               PASS
P1.2 stream/usage compatibility                    PASS
P1.2 second full live                              FAIL
P1.2 rollout TokenCount persistence diagnosis      CURRENT
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
