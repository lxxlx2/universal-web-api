# Codex Web Bridge Progress

## Branches

- stable verified base: `security-hardening`
- active V2 development: `codex-web-bridge-v2`
- V2 Draft PR: #2

## Verified macOS milestones

```text
Stage A-F protocol/CLI acceptance                    PASS
aggregate A-F checker                                PASS
Responses tool/call-id continuity                    PASS
P1.1 Responses compact direct live                   PASS
versioned lifecycle/provider switch CI/live          PASS
P1.2 stream compatibility CI/live                    PASS
P1.2 rollout TokenCount persistence                  PASS
P1.2 attempt-2 threshold diagnosis                   PASS
P1.2 small-step trigger implementation/CI #340       PASS
P1.2 native auto-compact trigger/local fallback live PASS
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

The fixed 20KB stress runner ended its last successful turn at active context `55,632`, below the 57,600 native auto-compact threshold. Exact Codex 0.153.4 source showed pre-turn compaction runs before the next user message is recorded, so the next fixed 20KB filler jumped across the threshold after the compact check. This attempt is classified as a runner threshold-crossing defect.

## Small-step native trigger probe

Tracked files:

- `tools/codex_auto_compact_trigger_probe.py`
- `tests/test_codex_auto_compact_trigger_probe.py`

Security hardening #340 / run `34161703429` passed before live validation.

The real macOS probe then produced:

```text
57429 < 57600
58290 > 57600
PRE_TRIGGER_OVER_HARD_CAP=NO
PRE_TRIGGER_ROLLOUT_COMPACT_MARKERS=0
TRIGGER_REPLY_EXACT=YES
TRIGGER_TOOL_EFFECTS=0
ROLLOUT_COMPACT_MARKER_DELTA=1
REMOTE_COMPACT_ROUTE_DELTA=0
REMOTE_COMPACT_SUCCESS_DELTA=0
TOKEN_LEAK_WORKSPACE=NO
AUTO_COMPACT_MODE=LOCAL_FALLBACK
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

Conclusion: native threshold detection, persisted TokenCount/resume restoration and Codex local fallback compaction are all live-PASS under UWA.

Detailed record: `docs/CODEX_P1_AUTO_COMPACT_TRIGGER_LIVE_PASS_2026-09-08.md`.

## Current gate: remote compact capability

Direct UWA `/v1/responses/compact` is already P1.1 PASS, but native Codex auto-compact still selects local fallback because the current custom provider is `RemoteCompactionSupport::Unsupported` in Codex 0.153.4.

Next work:

```text
exact 0.153.4 provider capability audit
→ identify narrow remote-compaction enablement
→ add regression coverage
→ CI
→ live threshold crossing
→ prove POST /v1/responses/compact route/success
→ compacted same-thread recovery
```

Do not rename the provider to `OpenAI` or `Azure` without first proving the full behavioral impact of those identities.

## Current status

```text
P1.1 compact endpoint + live protocol              PASS
versioned lifecycle/provider switch                PASS
P1.2 stream/usage compatibility                    PASS
P1.2 TokenCount persistence                        PASS
P1.2 native trigger/local fallback                 PASS
P1.2 remote compaction capability                  CURRENT
P1.3 affinity/restart/uncertain-effect              pending
Desktop UI live gate D1-D5                         pending / mandatory
```

## Production-hardening roadmap

```text
P1.2 remote compact capability + large-context recovery
P1.3 lost-affinity / restart + identity fencing + uncertain-effect recovery
Desktop D1-D5 actual UI acceptance
P1.4 real-project long-task pilot
P2 per-continuation serialization / queue planes / controlled-tab stale-result hardening
P3 MCP/plugin namespace + capability fidelity + multi-agent/tool fan-out
P4 Responses SSE slimming + bounded trace/transcript hygiene
P5 runtime/build identity + compatibility preflight + final regression/release checklist
```

## Recording discipline

Every live result, failure, repair and disruptive checkpoint is committed before the next step. README, canonical current state, this file, stage/failure records and Draft PR stay aligned.

## Final merge plan

Merge `codex-web-bridge-v2` into `main` only after P1 hardening, actual Desktop UI acceptance, the real-project pilot, final regression, CI, documentation and repository-safety checks are green.
