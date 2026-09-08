# Codex Web Bridge Progress

## Branches

- stable verified base: `security-hardening`
- active V2 development: `codex-web-bridge-v2`
- V2 Draft PR: #2

## Verified milestones

```text
Stage A-F protocol/CLI acceptance                    PASS
aggregate A-F checker                                PASS
P1.1 legacy Responses compact direct live            PASS
versioned lifecycle/provider switch CI/live          PASS
P1.2 stream/usage + TokenCount                       PASS
P1.2 native auto-compact trigger/local fallback live PASS
P1.2 remote capability shim implementation/CI #351   PASS
P1.2 remote V2 implementation/CI #380                PASS
P1.2 UWA provider precondition live                  PASS
UWA reasoning-effort semantics documented            PASS
```

## Native trigger live evidence

```text
57429 < 57600
58290 > 57600
ROLLOUT_COMPACT_MARKER_DELTA=1
REMOTE_COMPACT_ROUTE_DELTA=0
REMOTE_COMPACT_SUCCESS_DELTA=0
AUTO_COMPACT_MODE=LOCAL_FALLBACK
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

## Remote capability

Codex 0.153.4 recognizes configured OpenAI/Azure providers for remote compaction V2. `OpenAI` is too broad. A fail-closed helper changes only the managed UWA provider display name to `Azure`, preserving provider id, loopback endpoint, Responses wire API and disabled OpenAI auth.

Tracked files:

- `tools/codex_remote_compaction_compat.py`
- `tests/test_codex_remote_compaction_compat.py`
- `docs/CODEX_P1_REMOTE_COMPACTION_CAPABILITY_AUDIT_2026-09-08.md`

## Remote V2 implementation

Exact Codex 0.153.4 route:

```text
remote compact V2
→ prompt history + trailing compaction_trigger
→ ModelClientSession.stream()
→ ordinary Responses HTTP
→ /v1/responses
```

The implementation in `app/services/codex_remote_compaction_v2.py` now:

```text
valid trailing trigger
→ strip trigger
→ no-tools bounded ChatGPT Web compact summary
→ UWA versioned/bounded/integrity-checked opaque envelope
→ exactly one type=compaction output item
→ response.completed with non-zero usage
```

On future client-replayed compacted history, only valid UWA envelopes are decoded into model-visible compact context. Foreign/corrupt/oversized envelopes fail closed.

Exact 0.153.4 HTTP Responses requests do not use `previous_response_id`, so post-compact summary recovery is based on client-replayed compacted history rather than a compact-response server handle.

Live evidence now uses `tools/codex_remote_compaction_trigger_probe.py`, which counts V2-specific metadata markers rather than the legacy `/responses/compact` route.

CI history:

```text
#372 compile/public-safety PASS; lightweight CI dependency placement defect
#378 492 tests PASS; one wrapper test module-identity defect
#380 all jobs PASS
```

Run #380: `34185500715`.

## UWA provider precondition live

The initial remote-V2 live attempt was invalid because Codex was not using the managed UWA provider. The versioned provider switch has now been rerun and the full precondition contract passed:

```text
MODEL_PROVIDER_UWA=YES
MODEL_CHATGPT=YES
REASONING_HIGH=YES
APPROVAL_ON_REQUEST=YES
SANDBOX_WORKSPACE_WRITE=YES
PROVIDER_NAME_BASELINE=YES
LOOPBACK_BASE_URL=YES
WIRE_API_RESPONSES=YES
OPENAI_AUTH_DISABLED=YES
WEBSOCKETS_DISABLED=YES
UWA_PROVIDER_CONTRACT_PASS=YES
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
UWA_REMOTE_V2_PRECONDITION_PASS
```

Records:

- `docs/CODEX_P1_REMOTE_V2_LIVE_PRECONDITION_FAILURE_2026-09-08.md` — initial invalid attempt plus closed transient DNS blocker;
- `docs/CODEX_P1_REMOTE_V2_PRECONDITION_LIVE_PASS_2026-09-08.md` — successful UWA-mode precondition gate.

## Reasoning effort

The current bridge supports two real web reasoning modes, not three equivalent UI positions:

```text
High    supported and the managed UWA default
Medium  supported when the Responses request carries medium
Low     unsupported / fail closed
```

UWA applies Medium/High to ChatGPT Web and verifies the selected page state. The visual Codex Desktop slider alone is not proof that a reasoning change reached UWA. Add explicit Medium/High request+page verification to the Desktop gate.

Detailed semantics: `docs/CODEX_REASONING_EFFORT_SEMANTICS_2026-09-08.md`.

## External reference refresh

Reviewed/refreshed on 2026-09-08:

- `yyjeqhc/webcodex` through `79e61cc85008bf35e4eea02abd137531afdba968`;
- `Waishnav/devspace` at `d74ece04adc2a80ebed07c2798407b3be668b0f1`;
- `XiaoDuoYa/codex-with-chatgpt` at `a9f91cd98df1bc82686f57d5bc2b2993394c93be`;
- `alexanderradahl/mac-developer-bridge` at `fea70d1a3c5524164f2159f6063ba685fef91324`.

No architecture pivot. Official Codex remains the only local executor.

Roadmap additions:

```text
P1.3 typed bridge/session metadata outside model business tool args
P2 browser lease/generation/heartbeat/reclaim fencing
P2/P3 shared specialized-adapter governance
P3 protocol-edge version normalization / MCP-schema fidelity
P4 independent diff/test/tool evidence review + bounded sanitization/trust order
P5 doctor/preflight + verified disable path
P5 optional first-party ChatGPT page-runtime submission research
```

Detailed review: `docs/EXTERNAL_CODING_BRIDGE_REVIEW_2026-09-08.md`.

## Repository cleanup / standalone plan

The current repository is an actual fork of `lumingya/universal-web-api` and legitimately reuses upstream AGPL-3.0 browser/API/runtime code. The V2 branch also adds substantial project-specific Codex bridge implementation. The standalone project should say this clearly; no clean-room rewrite is required.

Do not prune the current fork during hardening. The standalone extraction begins only after the verified V2 release candidate is merged to `main`.

Planned post-main phases:

```text
S1 dependency/import audit + core manifest
S2 create clearer standalone repository
   - retain actually required upstream-derived runtime
   - retain AGPL/license/copyright attribution
   - add explicit UPSTREAM/attribution documentation
   - exclude unrelated generic UWA surface only when dependency proof allows
S3 rerun full CI + CLI/Desktop/live parity acceptance
S4 publish first standalone research release
```

The old fork remains available as development/provenance history at least through the first stable standalone release.

Detailed plan: `docs/POST_MAIN_STANDALONE_REPOSITORY_PLAN_2026-09-08.md`.

## Current gate: native remote compact macOS live

The UWA provider precondition is green and the live probe is currently being executed against the managed UWA provider + narrow Azure-name capability shim.

Required output:

```text
THRESHOLD_CROSSED=YES
PRE_TRIGGER_OVER_HARD_CAP=NO
ROLLOUT_COMPACT_MARKER_DELTA>=1
REMOTE_COMPACT_ROUTE_DELTA>=1
REMOTE_COMPACT_SUCCESS_DELTA>=1
AUTO_COMPACT_MODE=REMOTE
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

After that, run a separate same-thread recovery gate that recovers the first-turn conversation-only synthetic token through a real local write/read without searching local session/history stores.

## Current status

```text
P1.1 legacy compact endpoint/live                    PASS
P1.2 native trigger/local fallback                   PASS
P1.2 remote capability shim implementation/CI        PASS
P1.2 remote V2 implementation/CI                     PASS
P1.2 UWA provider precondition live                  PASS
P1.2 native remote compact live                      CURRENT
P1.2 same-thread post-remote recovery                pending
P1.3 affinity/restart/uncertain-effect               pending
Desktop Medium/High reasoning verification           pending / UI gate
Desktop UI live gate D1-D5                           pending / mandatory
post-main standalone repository extraction            planned
```

## Release and extraction order

```text
current P1.2 → P1.3 → P2-P5 → Desktop D1-D5 → real-project pilot
→ final regression / public-repo safety / docs
→ merge verified V2 to main
→ S1 core dependency audit
→ S2 standalone attributed extraction
→ S3 parity acceptance
→ S4 standalone research release
```

## Recording discipline

Every live result, failure, repair and disruptive checkpoint is committed before the next step. README, canonical current state, this file, stage/failure records and Draft PR stay aligned. Merge to `main` only after all mandatory gates are green.
