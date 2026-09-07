# Codex Web Bridge current state

Canonical handoff for `codex-web-bridge-v2`.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while routing model inference through UWA to logged-in ChatGPT Web. Codex remains authoritative for filesystem, shell, edits, tests, Git, sandbox and approval.

The production target explicitly includes normal use from ChatGPT Desktop in Codex mode. CLI/protocol acceptance remains necessary evidence, but it is not sufficient proof of Desktop UI compatibility.

## Verified live acceptance

```text
single-file coding loop                    PASS
Stage A multi-file read/edit/test          PASS
Stage B failure recovery                   PASS
Stage C Git diff discipline                PASS
Stage D long process + write_stdin         PASS
Stage E same-thread context                PASS
Stage F Codex + UWA restart continuity     PASS
aggregate A-F checker                      PASS
real exec_command / native cwd             PASS
Responses tool round trip                  PASS
required-tool enforcement                  PASS
call-id / web-session continuation         PASS
P1.1 Responses compact direct live         PASS
versioned UWA lifecycle CI/live            PASS
versioned UWA provider switch CI/live      PASS
P1.2 stream compatibility CI #313          PASS
P1.2 non-zero usage macOS smoke            PASS
Codex Desktop UI live gate                 REQUIRED / pending
```

## P1.1 compact protocol: PASS

`POST /v1/responses/compact` is implemented and direct macOS live validation returned HTTP 200 with valid compact output after the stale-listener incident was repaired. Detailed records remain in the P1.1 incident and lifecycle documents.

## Versioned lifecycle/provider switch: PASS

UWA lifecycle, provider switching and Memories handling are repository-managed. The normal `codex-uwa` path no longer executes `~/.uwa/config_switch.py`. Real macOS validation proved listener replacement, provider contract preservation, restore state and healthy UWA/browser state.

## Current gate: P1.2 native Codex large-context compaction / recovery

### First full live attempt

The first macOS P1.2 run completed the seed and seven filler turns, then round 8 failed with `idle timeout waiting for SSE`. Successful turns also reported all-zero Responses usage.

Two protocol repairs followed:

1. comment-only heartbeats were replaced with real `response.in_progress` SSE events so Codex's parsed-event idle timer sees activity;
2. when real non-zero usage is unavailable, UWA supplies a bounded conservative local usage estimate so Codex can observe context growth.

The failed-turn evidence path was also repaired. Security hardening CI #313 passed, and a real macOS smoke then proved:

```text
LISTENER_REPLACED=YES
SERVICE=healthy
BROWSER_CONNECTED=True
INPUT_TOKENS=7113
OUTPUT_TOKENS=54
NONZERO_USAGE=YES
USAGE_SMOKE_PASS=YES
CODEX_USAGE_MARKERS=1
P1_STREAM_USAGE_SMOKE_PASS
```

### Second full live attempt: FAIL / diagnosis current

With the repaired runtime, the same-thread filler run produced positive growing input usage:

```text
round 01   21230
round 02   42219
round 03   70125
round 04  104948
round 05  146688
round 06  195345
round 07  250919
```

All seven completed filler turns had zero local tool effects. Yet every current-run compact counter remained zero:

```text
COMPACT_ROUTE_DELTA=0
COMPACT_SUCCESS_DELTA=0
```

Round 8 then failed the filler contract (`ACK_EXACT=NO`, no tool effects, no compact marker).

The important new upstream finding is confirmed against the exact installed Codex release source, not only upstream `main`: `rust-v0.153.4` resolves to commit `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`.

In Codex 0.153.4, configured providers advertise remote compaction only when either:

```text
provider.name == "OpenAI"
OR
is_azure_responses_provider(provider.name, provider.base_url)
```

The current UWA provider is named `Universal Web API` at localhost, so Codex classifies it as `RemoteCompactionSupport::Unsupported`. That directly explains why native auto-compaction cannot select the remote `/v1/responses/compact` implementation under the current provider identity.

Codex 0.153.4 does have a local summary-compaction fallback for unsupported providers, and its pre-turn logic should invoke an auto-compaction path once the active context reaches the model token limit. Before changing provider identity, the next diagnostic must determine:

1. the model context window actually used by the running Codex thread, not merely the 64K value returned by UWA's `/v1/models` endpoint;
2. whether any local fallback compaction occurred but was invisible to the current remote-route-only evidence counters;
3. whether the on-disk/in-memory Codex model catalog cache differs from the current UWA model catalog.

Do not blindly rerun the 24-round stress test before these are resolved.

Detailed P1.2 records:

- `docs/CODEX_P1_LARGE_CONTEXT_ACCEPTANCE_2026-09-08.md`
- `docs/CODEX_P1_LARGE_CONTEXT_LIVE_FAILURE_2026-09-08.md`
- `docs/CODEX_P1_LARGE_CONTEXT_SECOND_LIVE_FAILURE_2026-09-08.md`
- `docs/CODEX_P1_STREAM_COMPAT_REPAIR_2026-09-08.md`
- `docs/CODEX_P1_STREAM_USAGE_LIVE_SMOKE_2026-09-08.md`

## Current status

```text
P1.1 compact endpoint + direct live             PASS
versioned lifecycle/provider switch             PASS
P1.2 stream/usage compatibility CI/live         PASS
P1.2 second full large-context live             FAIL
P1.2 Codex provider capability/cache diagnosis  CURRENT
P1.3 lost-affinity/restart fallback             pending / expanded
Desktop UI D1-D5                                pending / mandatory before main
```

## WebCodex design review

`yyjeqhc/webcodex` remains an Apache-2.0 design reference. Official Codex stays the local execution authority. Reliability lessons incorporated into later gates include uncertain-effect reconciliation, separate identity domains, generation fencing, bounded diagnostics and distinct concurrency planes.

## Continuity layers

1. Codex Desktop / CLI thread history.
2. Private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Git-tracked handoff documents as long-term project truth.

## Production-hardening order

```text
P1.2 native Codex large-context compaction / stress / recovery
P1.3 lost-affinity / restart + identity fencing + uncertain-effect recovery
Desktop UI live acceptance D1-D5
P1.4 real-project long-task pilot
P2 per-continuation serialization / queue planes / controlled-tab stale-result hardening
P3 MCP/plugin namespace, capability fidelity and multi-agent/tool fan-out
P4 Responses SSE slimming, bounded trace and transcript hygiene
P5 runtime/build identity, compatibility preflight, final regression and release checklist
```

## Collaboration rule

Every completed stage, important failure, repair and disruptive checkpoint is committed before moving on. README, this canonical state, progress tracking, stage/failure records and Draft PR should remain aligned.

## Merge policy

Do not merge into `main` yet. Merge only after P1 hardening, Desktop UI acceptance, the real-project pilot, final regression, CI, documentation and public-repository safety checks are green.

## Public repository safety

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, Codex memory workspace content, or private project source captured during acceptance.
