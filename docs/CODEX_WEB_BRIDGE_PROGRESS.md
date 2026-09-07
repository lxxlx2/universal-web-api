# Codex Web Bridge Progress

## Branches

- stable verified base: `security-hardening`
- active V2 development: `codex-web-bridge-v2`
- V2 Draft PR: #2

## Verified macOS milestones

```text
single-file coding loop                     PASS
Stage A multi-file coding loop              PASS
Stage B failure recovery                    PASS
Stage C Git diff discipline                 PASS
Stage D long process + write_stdin          PASS
Stage E same-thread context continuity      PASS
Stage F Codex + UWA restart continuity      PASS
aggregate A-F checker                       PASS
real exec_command / native cwd              PASS
Responses function_call round trip          PASS
required-tool repair                        PASS
duplicate required-tool suppression         PASS
call-id continuation affinity               PASS
single-tool / single-web-conversation gate  PASS
P1.1 Responses compact direct live          PASS
versioned UWA lifecycle CI                  PASS
versioned UWA lifecycle macOS live          PASS
versioned UWA provider switch CI            PASS
versioned UWA provider switch macOS live    PASS
P1.2 automated runner CI                    PASS
P1.2 stream compatibility CI #313           PASS
P1.2 non-zero usage macOS smoke             PASS
```

Evidence note: the final Stage E/F runs were audited primarily through `codex exec` / `codex exec resume`. They close the protocol/CLI continuity gate but do not close actual ChatGPT Desktop UI acceptance. A mandatory Desktop D1-D5 gate is tracked in `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`.

## P1 compact protocol: CLOSED PASS

P1.1 implemented `/v1/responses/compact` and direct macOS validation returned HTTP 200 with valid compact output after the stale-listener lifecycle defect was repaired.

## Lifecycle/provider switch: CLOSED PASS

Lifecycle, Memories handling, and UWA provider switching are repository-managed. The normal `codex-uwa` path no longer executes `~/.uwa/config_switch.py`. CI and macOS live validation proved listener replacement, provider contract preservation, restore state, and healthy UWA/browser state.

## WebCodex architecture review

`yyjeqhc/webcodex` was reviewed as an Apache-2.0 design reference. Official Codex remains the local executor. Reliability lessons incorporated into later gates include request-loss versus execution-loss separation, uncertain-effect reconciliation, identity/generation fencing, bounded diagnostics and distinct concurrency planes.

## P1.2 live history

### Attempt 1

Seed plus seven filler continuations succeeded. Round 8 failed with SSE idle timeout. Successful turns exposed all-zero Responses token usage.

Repairs:

- comment heartbeat -> parseable `response.in_progress` SSE heartbeat;
- conservative fallback usage only when real non-zero usage is unavailable;
- failed-turn UWA evidence harvesting.

Security hardening CI #313 passed. A real macOS smoke then proved the repaired runtime was loaded and Codex received non-zero usage (`input_tokens=7113`, `output_tokens=54`).

### Attempt 2

The repaired full run produced monotonically growing input usage:

```text
21230 -> 42219 -> 70125 -> 104948 -> 146688 -> 195345 -> 250919
```

Rounds 1-7 returned exact filler ACKs with zero tool effects, but every current-run remote compact counter remained zero. Round 8 failed the filler contract.

Detailed record: `docs/CODEX_P1_LARGE_CONTEXT_SECOND_LIVE_FAILURE_2026-09-08.md`.

## Exact Codex 0.153.4 upstream diagnosis

The installed client version is `0.153.4`. Upstream tag `rust-v0.153.4` resolves to commit `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`.

That exact release advertises remote compaction only when a configured provider is recognized as OpenAI or Azure. The current UWA provider is named `Universal Web API` and uses a localhost base URL, so Codex classifies it as `RemoteCompactionSupport::Unsupported`.

This explains why the auto-compaction selector cannot choose the remote `/v1/responses/compact` implementation under the current provider identity. Codex 0.153.4 does retain a local summary-compaction fallback for unsupported providers.

Before changing provider identity, the current diagnostic must determine:

1. the context window actually used by the live Codex thread, not only the 64K value exposed by UWA `/v1/models`;
2. whether local fallback compaction occurred but was invisible to the remote-route-only acceptance counters;
3. whether `~/.codex/models_cache.json` differs from the current UWA model catalog;
4. whether a top-level Codex config override changes context/auto-compact behavior.

Do not repeat the full stress run until these facts are known.

## Current gate

```text
Stage A-F protocol/CLI acceptance                PASS
aggregate A-F checker                            PASS
P1.1 compact endpoint + live protocol            PASS
versioned lifecycle/provider switch              PASS
P1.2 stream/usage compatibility                  PASS
P1.2 second full live                            FAIL
P1.2 provider capability / model-cache diagnosis CURRENT
P1.3 affinity/restart/uncertain-effect            pending
Desktop UI live gate D1-D5                       pending / mandatory
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

Merge `codex-web-bridge-v2` into `main` only after P1 hardening, actual Desktop UI acceptance, the real-project pilot, final regression, CI, documentation and repository-safety checks are green and the handoff documentation is current.
