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
P1.2 native auto-compact trigger/local fallback live PASS
P1.2 remote-capability shim implementation/CI #351   PASS
```

Stage E/F remain protocol/CLI evidence and do not close the mandatory Desktop D1-D5 gate.

## P1.2 live history

Attempt 1 exposed SSE idle heartbeat and all-zero usage compatibility gaps; both are repaired and live-validated.

Attempt 2 used a fixed 20KB step and was reclassified as an acceptance threshold-crossing defect after exact Codex 0.153.4 source/rollout analysis.

The dedicated small-step live probe then proved native threshold triggering and local fallback:

```text
57429 < 57600
58290 > 57600
PRE_TRIGGER_OVER_HARD_CAP=NO
ROLLOUT_COMPACT_MARKER_DELTA=1
REMOTE_COMPACT_ROUTE_DELTA=0
REMOTE_COMPACT_SUCCESS_DELTA=0
AUTO_COMPACT_MODE=LOCAL_FALLBACK
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

Detailed live record: `docs/CODEX_P1_AUTO_COMPACT_TRIGGER_LIVE_PASS_2026-09-08.md`.

## Remote capability gate

Exact `rust-v0.153.4` source established that configured providers get remote V2 compaction when recognized as OpenAI or Azure. `OpenAI` is too broad. The chosen narrow shim changes only the managed provider display name to `Azure`, while preserving provider id `uwa`, loopback base URL, Responses wire API, disabled OpenAI auth and all unrelated config.

Tracked implementation:

- `tools/codex_remote_compaction_compat.py`
- `tests/test_codex_remote_compaction_compat.py`
- `docs/CODEX_P1_REMOTE_COMPACTION_CAPABILITY_AUDIT_2026-09-08.md`

The helper fails closed unless the complete managed UWA provider contract matches. Security hardening #351 / run `34164070091`, head `127ed09fbb1f8941ff4332db72bf498fb9f80287`, completed `success`.

Known compatibility tradeoff: `codex doctor` treats the provider as Azure and skips its own `/models` reachability probe. Normal runtime models management still uses the configured UWA endpoint.

## Current gate

Real macOS native remote-compaction validation:

```text
enable versioned compatibility shim
→ verify provider id/base URL/auth/wire remain exact
→ small-step threshold crossing
→ native Codex calls /v1/responses/compact
→ remote compact success marker
→ rollout compact lifecycle marker
```

Required immediate PASS markers include:

```text
REMOTE_COMPACT_ROUTE_DELTA>=1
REMOTE_COMPACT_SUCCESS_DELTA>=1
AUTO_COMPACT_MODE=REMOTE
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

After this gate, run same-thread post-compact synthetic-token recovery with real local write/read before closing P1.2.

## Current status

```text
P1.1 compact endpoint + live protocol              PASS
versioned lifecycle/provider switch                PASS
P1.2 stream/usage compatibility                    PASS
P1.2 TokenCount persistence                        PASS
P1.2 native trigger/local fallback                 PASS
P1.2 remote capability shim implementation/CI      PASS
P1.2 native remote compact macOS live              CURRENT
P1.3 affinity/restart/uncertain-effect              pending
Desktop UI live gate D1-D5                         pending / mandatory
```

## Production-hardening roadmap

```text
P1.2 native remote compact + same-thread recovery
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
