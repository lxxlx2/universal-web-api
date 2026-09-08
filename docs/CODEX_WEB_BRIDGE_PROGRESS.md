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
P1.2 remote capability shim implementation/CI        PASS
P1.2 remote V2 implementation/CI                     PASS
P1.2 UWA provider precondition live                  PASS
P1.2 native remote V2 compaction macOS live          PASS
P1.2 same-thread token continuity live               PASS
P1.2 body-after-prefix anti-thrash migration live    PASS
P1.2 deterministic staged recovery harness CI #473   PASS
P1.3 lost-affinity/restart fallback CI #478           PASS
P1.3 stable identity/stale fencing CI #483           PASS
P1.3 uncertain tool-effect retry safety CI #486      PASS
Hybrid H0 metadata route audit                       PASS / CI
Hybrid H1 exact route/model/effort guard             PASS / CI
Hybrid H2 fresh Desktop route probe                  PASS / LIVE
Desktop D1 real local-tool round trip                PASS / LIVE
UWA reasoning-effort semantics documented            PASS
```

## P1.2 closure evidence

Native Codex CLI 0.153.4 remote-V2 compaction was proven through the managed UWA provider:

```text
AUTO_COMPACT_LIMIT=57600
HARD_CONTEXT_LIMIT=60800
PRE_TRIGGER_ACTIVE_TOKENS=57674
PRE_TRIGGER_OVER_HARD_CAP=NO
TRIGGER_REPLY_EXACT=YES
TRIGGER_TOOL_EFFECTS=0
ROLLOUT_COMPACT_MARKER_DELTA=1
REMOTE_COMPACT_ROUTE_DELTA=1
REMOTE_COMPACT_SUCCESS_DELTA=1
TOKEN_LEAK_WORKSPACE=NO
AUTO_COMPACT_MODE=REMOTE
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

Post-compaction live recovery then proved:

```text
same private Codex thread resumed                    YES
conversation-only token recovered                    YES
real local write                                     YES
result exact                                         YES
private history search                               NO
compaction marker growth during decisive recovery    NO
```

The repeated post-compact compaction loop was eliminated by managing Codex's supported UWA-only setting:

```toml
model_auto_compact_token_limit_scope = "body_after_prefix"
```

Provider switching preserves the user's pre-UWA value and restores it on official mode. The old one-turn guard -> write -> read choreography is no longer treated as the product continuity criterion; a deterministic staged harness now covers those three client-tool steps as separate bounded resumed turns and passed complete CI #473.

P1.2 / M1 is PASS / CLOSED.

Detailed records:

- `docs/CODEX_P1_REMOTE_V2_LIVE_PASS_2026-09-08.md`
- `docs/CODEX_P1_REMOTE_V2_RECOVERY_TOKEN_CONTINUITY_PASS_2026-09-08.md`
- `docs/CODEX_P1_BODY_AFTER_PREFIX_LIVE_MIGRATION_PASS_2026-09-08.md`
- `docs/CODEX_P1_REMOTE_V2_RECOVERY_CLOSED_2026-09-08.md`

## P1.3 closure evidence

The accelerated continuity gate was deliberately limited to three correctness blockers. All are now closed:

```text
lost-affinity / UWA restart fallback                 PASS
stable continuation identity / stale fencing         PASS
uncertain tool-effect retry safety                   PASS
```

The live Stage F restart already proved real recovery after process-local affinity was lost. Focused regressions now guarantee persisted-history fallback, fail-closed orphan tool output handling, immutable response/conversation binding, conflicting call-id fencing, no retry after a real function call, no retry after response.failed, and bounded repair only before any client tool effect can occur.

Full Security hardening CI runs #478, #483 and #486 passed across public-repo-safety, Ubuntu/macOS and upstream regression jobs.

P1.3 / M2 is PASS / CLOSED.

Detailed closure: `docs/CODEX_P1_3_MINIMAL_CONTINUITY_CLOSED_2026-09-08.md`.

## Current gate: Hybrid Routing Safety + Desktop UI

A pre-D1 event confirmed an existing Desktop thread as `openai / gpt-6-astra / ultra` while earlier sessions were `uwa / chatgpt / high`. The resumed official thread consumed official allowance. D1 itself had not started.

This proves that configured provider state alone cannot tell the operator which route an existing Desktop thread will use. The release now has a narrow Hybrid Routing Safety block inside M3.

H2 passed on a fresh Desktop thread. The post-marker route audit proved `uwa / chatgpt / high`, healthy UWA/browser state, one fresh UWA request/response pair, completed status, and an exact route expectation PASS. This closed the fresh-thread ambiguity and allowed the original Desktop acceptance path to resume.

D1 has now also passed through the actual Codex Desktop UI. The independent checker returned `multi_file: PASS` and `ACCEPTANCE_PASS`; only `multi_file/math_ops.py` and `multi_file/summary.py` changed; test files remained unchanged. The D1 route remained `uwa / chatgpt / high` with four post-marker UWA request/response pairs and exact route expectation PASS. Metadata-only traces proved three real `exec_command` function calls and a completed Responses turn.

Detailed D1 record: `docs/CODEX_DESKTOP_D1_LIVE_PASS_2026-09-08.md`.

Current status:

```text
H0 metadata-only route audit helper                     PASS / CI
H1 exact provider/model/effort fail-closed guard         PASS / CI
H2 tiny fresh Desktop route probe                        PASS / LIVE / CLOSED
H3 explicit official -> UWA stateful handoff             pending
H4 private metadata-only transition ledger               marker foundation present
H5 synthetic hybrid acceptance                           pending
D1 real Desktop local tool round trip                     PASS / LIVE / CLOSED
D2 same Desktop thread continuation                      READY / CURRENT
D3 full Desktop app restart + history resume             pending
D4 Desktop + UWA restart + same-thread recovery          pending
D5 clean official-account restore                        pending
Medium/High request/page verification                    folded into Desktop gate
```

`tools/codex_route_audit.py` intentionally uses only authoritative Codex metadata events and UWA metadata-only traces. It never recursively searches rollout bodies, and UWA expectation PASS requires a real post-marker UWA wire request. Exact expected provider/model/effort values act as the first-release quality floor: a long task must not start on an unproven or weaker route.

Detailed routing design: `docs/CODEX_HYBRID_ROUTING_SAFETY_2026-09-08.md`.
CI record: `docs/CODEX_HYBRID_ROUTE_AUDIT_CI_PASS_2026-09-08.md`.
H2 live record: `docs/CODEX_HYBRID_H2_FRESH_ROUTE_PROBE_PASS_2026-09-08.md`.
D1 live record: `docs/CODEX_DESKTOP_D1_LIVE_PASS_2026-09-08.md`.

## Accelerated release-critical path

```text
M1 P1.2 same-thread post-remote recovery                  PASS / CLOSED
M2 P1.3 minimal continuity blockers                       PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                           CURRENT; H0-H2 PASS
M3b Desktop UI D1-D5 + Medium/High verification           CURRENT; D1 PASS, D2 CURRENT
M4 one real-project long-task pilot
M5 final A-F + compaction + restart regression
M6 CI green + public-repo safety + docs/provenance/license checks
M7 branch-topology inspection + merge verified V2 to main
```

Moved to post-main hardening unless required by a failure in M3-M6:

```text
broad P2 concurrency / browser-lease governance
broad P3 MCP/schema/capability normalization
expanded P4 evidence/trust-order framework
full P5 doctor/preflight productization
fully automatic unsupported/private quota polling
background automatic thread migration
provider cost optimization / generalized routing engine
rich routing dashboard / automatic task classifier
optional first-party ChatGPT page-runtime research
broad cleanup of unrelated generic upstream UWA surface
```

The fast-release strategy is unchanged: only the minimal route-safety layer required to prevent silent premium quota spend or silent model downgrade was added to the merge-critical path.

## Reasoning effort

```text
High    supported and managed-UWA default
Medium  supported when the Responses request carries medium
Low     unsupported / fail closed
```

UWA applies Medium/High to ChatGPT Web and verifies the page state. Cross-provider model families are not treated as numerically equivalent. If a task requires an exact official model/reasoning tier or exact UWA route, that expectation must be proven before the long task starts.

Detailed semantics: `docs/CODEX_REASONING_EFFORT_SEMANTICS_2026-09-08.md`.

## External reference refresh

Reviewed/refreshed `yyjeqhc/webcodex`, `Waishnav/devspace`, `XiaoDuoYa/codex-with-chatgpt`, and `alexanderradahl/mac-developer-bridge`. No architecture pivot: Codex remains the local executor.

Useful reliability ideas remain tracked for post-main hardening, but feature parity with adjacent projects is not a merge blocker.

Detailed review: `docs/EXTERNAL_CODING_BRIDGE_REVIEW_2026-09-08.md`.

## Repository cleanup / standalone plan

The current repository is an actual fork of `lumingya/universal-web-api` and legitimately reuses upstream AGPL-3.0 browser/API/runtime code. The V2 branch also adds substantial project-specific Codex bridge implementation. No clean-room rewrite is required.

Do not prune the current integration fork before the release gate. After verified V2 is merged to `main`:

```text
S1 dependency/import/runtime audit + core manifest
S2 create clearer standalone attributed repository
S3 rerun full CI + CLI/Desktop/live parity acceptance
S4 publish first standalone research release
```

Detailed plan: `docs/POST_MAIN_STANDALONE_REPOSITORY_PLAN_2026-09-08.md`.

## Current status

```text
P1.1 legacy compact endpoint/live                    PASS
P1.2 native trigger/local fallback                   PASS
P1.2 remote capability shim implementation/CI        PASS
P1.2 remote V2 implementation/CI                     PASS
P1.2 UWA provider precondition live                  PASS
P1.2 native remote compact live                      PASS
P1.2 same-thread post-remote recovery                PASS / CLOSED
P1.3 minimal continuity blockers                     PASS / CLOSED
Hybrid Routing Safety H0-H2                         PASS
Hybrid Routing Safety H3-H5                         CURRENT / mandatory
Desktop UI D1                                       PASS / CLOSED
Desktop UI D2-D5 + Medium/High verification          CURRENT / mandatory; D2 READY
real-project long-task pilot                         pending / mandatory
final regression / safety / docs                     pending / mandatory
post-main standalone repository extraction           planned
```

## Recording discipline

Every live result, failure, repair and disruptive checkpoint is committed before the next step. README, canonical current state, this file, stage/failure records and Draft PR stay aligned as far as the available GitHub integration safely allows.
