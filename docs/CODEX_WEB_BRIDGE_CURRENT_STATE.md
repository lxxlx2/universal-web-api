# Codex Web Bridge current state

Canonical handoff for `codex-web-bridge-v2`.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while supporting a controlled UWA fallback to logged-in ChatGPT Web. Codex remains authoritative for filesystem, shell, edits, tests, Git, sandbox and approval. Provider/model routing must be visible and auditable before long work starts; CLI/protocol acceptance is necessary but does not replace the mandatory Desktop UI gate.

## Verified acceptance / CI

```text
Stage A-F protocol/CLI acceptance                    PASS
aggregate A-F checker                                PASS
Responses tool / call-id continuity                  PASS
P1.1 Responses compact direct live                   PASS
versioned UWA lifecycle/provider switch CI/live      PASS
P1.2 stream/usage compatibility                      PASS
P1.2 rollout TokenCount persistence                  PASS
P1.2 native auto-compact trigger/local fallback      PASS
P1.2 remote-capability shim implementation/CI        PASS (#351)
P1.2 remote V2 protocol implementation/CI            PASS (#380)
P1.2 UWA provider precondition live                  PASS
P1.2 native remote V2 compaction macOS live          PASS
P1.2 same-thread post-remote token continuity live   PASS
P1.2 body-after-prefix anti-thrash migration live    PASS
P1.2 deterministic staged recovery harness CI        PASS (#473)
P1.3 lost-affinity/restart fallback                  PASS (#478)
P1.3 stable identity/stale fencing                   PASS (#483)
P1.3 uncertain tool-effect retry safety              PASS (#486)
local provider/model/effort metadata distinction     PASS
UWA reasoning-effort semantics documented            PASS
Hybrid Routing Safety                                CURRENT / REQUIRED
Codex Desktop UI live gate                           CURRENT / REQUIRED
```

## P1.2 native remote V2 compaction: CLOSED

The valid macOS run used Codex CLI 0.153.4, the managed UWA provider, and the narrow Azure-name capability shim. The probe crossed the native auto-compaction threshold without crossing the hard effective context cap:

```text
AUTO_COMPACT_LIMIT=57600
HARD_CONTEXT_LIMIT=60800
PRE_TRIGGER_ACTIVE_TOKENS=57674
PRE_TRIGGER_OVER_HARD_CAP=NO
```

The trigger produced the required remote-V2 evidence:

```text
TRIGGER_REPLY_EXACT=YES
TRIGGER_TOOL_EFFECTS=0
ROLLOUT_COMPACT_MARKER_DELTA=1
REMOTE_COMPACT_ROUTE_DELTA=1
REMOTE_COMPACT_SUCCESS_DELTA=1
TOKEN_LEAK_WORKSPACE=NO
AUTO_COMPACT_MODE=REMOTE
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

Post-compaction recovery then proved same-thread continuity and conversation-only token recovery. The decisive recovery run produced a real local write containing the recovered token, an exact result file, no private history search, and no additional compaction marker. UWA mode now manages Codex's supported `model_auto_compact_token_limit_scope="body_after_prefix"` override and restores the user's original scope when switching back to official mode.

The earlier single-turn guard -> write -> read choreography was separated from the product-continuity claim because the model can legally skip intermediate acceptance choreography while still proving continuity. A deterministic staged harness now validates guard/write/read as three bounded resumed turns and is covered by complete CI.

Detailed records:

- `docs/CODEX_P1_REMOTE_V2_LIVE_PASS_2026-09-08.md`
- `docs/CODEX_P1_REMOTE_V2_RECOVERY_TOKEN_CONTINUITY_PASS_2026-09-08.md`
- `docs/CODEX_P1_BODY_AFTER_PREFIX_LIVE_MIGRATION_PASS_2026-09-08.md`
- `docs/CODEX_P1_REMOTE_V2_RECOVERY_CLOSED_2026-09-08.md`

P1.2 / merge-critical M1 is PASS / CLOSED.

## P1.3 minimal continuity blockers: CLOSED

Accelerated P1.3 was intentionally limited to correctness blockers that could corrupt, duplicate or mis-associate work across restart/lost-affinity boundaries. All three are now closed:

```text
lost-affinity / UWA-restart fallback correctness          PASS
stable continuation identity / stale-generation fencing   PASS
uncertain tool-effect reconciliation before retry          PASS
```

Evidence includes the real Stage F UWA restart recovery, focused fallback regressions, immutable response/conversation binding, conflicting call-id fencing, bounded required-tool retry rules and full Security hardening CI runs #478, #483 and #486.

Detailed closure: `docs/CODEX_P1_3_MINIMAL_CONTINUITY_CLOSED_2026-09-08.md`.

## Hybrid Routing Safety: CURRENT

A pre-D1 Desktop event proved that an already-existing Desktop conversation can resume through the official provider even while the machine also has UWA-backed sessions/configuration. Local metadata confirmed the quota-consuming resumed task as:

```text
provider=openai
model=gpt-6-astra
effort=ultra
```

and earlier UWA sessions as:

```text
provider=uwa
model=chatgpt
effort=high
```

Therefore `~/.codex/config.toml` is not sufficient proof of the active Desktop thread's route. The product target is now an explicit hybrid mode:

```text
official route intentionally selected and acceptable
→ use official allowance knowingly

official exhausted/unavailable or explicit handoff
→ preserve workspace/Git state
→ switch to UWA
→ prove fresh UWA route
→ continue in a fresh UWA thread using a local-only handoff checkpoint
```

Release-critical minimal scope:

```text
H0 metadata-only route audit helper
H1 explicit route intent + fail-closed quality floor
H2 tiny fresh-thread route probe before long Desktop work
H3 explicit official -> UWA workspace handoff
H4 private metadata-only transition ledger
H5 synthetic live acceptance for routing/handoff
```

No silent premium-quota spend and no silent quality downgrade are allowed. Unknown quota state must not be guessed. Broad automatic routing remains post-main.

Detailed design: `docs/CODEX_HYBRID_ROUTING_SAFETY_2026-09-08.md`.

## Current gate: Hybrid Routing Safety + Desktop UI

The active merge-critical gate remains M3, now split into a narrow routing-safety block and the actual Desktop scenarios:

```text
M3a H0-H5 Hybrid Routing Safety                         CURRENT
M3b D1 real Desktop local tool round trip              blocked on fresh route probe
     D2 same Desktop thread continuation               pending
     D3 full Desktop app restart + history resume      pending
     D4 Desktop + UWA restart + same-thread recovery   pending
     D5 clean official-account restore                 pending
     Medium/High request -> ChatGPT Web verification   folded into Desktop gate
```

A long D1 task must not run until a tiny fresh Desktop thread proves the intended provider/model/effort with metadata-only evidence.

## Accelerated main-merge path

The project is still release-focused. Broad P2-P5 feature expansion and broad routing automation do not block the first verified merge to `main` unless a remaining live gate exposes a dependency on them.

Merge-blocking sequence:

```text
M1 P1.2 same-thread post-remote recovery                  PASS / CLOSED
M2 P1.3 minimal continuity blockers                       PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                           CURRENT
M3b Desktop UI D1-D5                                      CURRENT after route probe
M4 one real-project long-task pilot
M5 final A-F + compaction + restart regression
M6 CI green + public-repo safety + docs/provenance/license checks
M7 inspect branch topology and merge verified V2 to main
```

Moved to post-main hardening unless required by an observed blocker:

```text
broad P2 concurrency/governance framework
broad P3 MCP/schema/capability normalization
expanded P4 evidence/trust framework
full P5 doctor/preflight productization
fully automatic unsupported/private quota polling
background automatic thread migration
provider cost optimization / generalized policy engine
rich routing dashboard / task classifier
optional first-party page-runtime research
broad upstream-surface cleanup
```

Detailed decision: `docs/ACCELERATED_MAIN_MERGE_GATE_2026-09-08.md`.

## Reasoning-effort semantics

UWA treats the actual Responses request plus verified ChatGPT Web state as authoritative, not the visible position of a Desktop slider by itself.

```text
UWA default                       high
request effort=medium             supported -> verify Medium / 中 on ChatGPT Web
request effort=high               supported -> verify High / 高 on ChatGPT Web
request effort=low/light          unsupported / fail closed
```

The managed UWA provider defaults to `model_reasoning_effort="high"`. Medium and High are intentionally distinct bridge modes. Desktop Medium/High request+page verification is folded into the mandatory Desktop UI gate.

Detailed record: `docs/CODEX_REASONING_EFFORT_SEMANTICS_2026-09-08.md`.

## Adjacent bridge design refresh

Reviewed/refreshed references include `yyjeqhc/webcodex`, `Waishnav/devspace`, `XiaoDuoYa/codex-with-chatgpt`, and `alexanderradahl/mac-developer-bridge`.

Decision: no architecture pivot. Official Codex remains the local executor. Useful reliability ideas are tracked for post-main hardening, but adjacent-project feature parity does not enter the current release-critical path.

Detailed review: `docs/EXTERNAL_CODING_BRIDGE_REVIEW_2026-09-08.md`.

## Repository provenance and post-main standalone extraction

The current GitHub repository is an actual fork of `lumingya/universal-web-api` and retains upstream AGPL-3.0 code/history. It also contains substantial newly implemented Codex bridge implementation.

After the verified V2 release candidate is merged to `main`, create a clearer standalone research repository by dependency-auditing and extracting the bridge core plus genuinely required upstream runtime. Preserve AGPL-3.0, copyright/license notices and explicit upstream attribution; do not rewrite working upstream-derived foundations merely to remove provenance.

Post-main phases:

```text
S1 dependency/import/runtime audit + core manifest
S2 create standalone attributed repository
S3 full CI/live parity acceptance
S4 first standalone research release
```

Detailed plan: `docs/POST_MAIN_STANDALONE_REPOSITORY_PLAN_2026-09-08.md`.

## Current status

```text
P1.1 legacy compact endpoint/direct live             PASS
P1.2 native threshold/local fallback                 PASS
P1.2 remote capability shim implementation/CI        PASS
P1.2 remote V2 ordinary Responses implementation/CI  PASS
P1.2 UWA provider precondition live                  PASS
P1.2 native remote compact macOS live                PASS
P1.2 same-thread post-remote recovery                PASS / CLOSED
P1.3 minimal continuity blockers                     PASS / CLOSED
Hybrid Routing Safety H0-H5                          CURRENT / mandatory
Desktop UI D1-D5 + Medium/High verification          CURRENT / mandatory
real-project pilot                                   pending / mandatory
final regression/safety/docs                         pending / mandatory
post-main standalone repository extraction           planned
```

## Continuity layers

1. Codex Desktop / CLI thread history.
2. UWA private Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Local-only hybrid handoff/route metadata under `~/.uwa`.
5. Git-tracked handoff documents as long-term project truth.

## Collaboration / merge / safety

Every completed stage, important failure, repair and disruptive checkpoint is committed before moving on. README, this canonical state, progress tracking, stage/failure records and Draft PR stay aligned as far as the available GitHub integration safely allows.

Do not merge into `main` until the accelerated merge-blocking sequence is green. P2-P5 enhancements and broad routing automation continue after the first verified `main` baseline unless a remaining gate proves one is required earlier.

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, Codex memory workspace content, local hybrid handoff prompts, or private project source captured during acceptance.
