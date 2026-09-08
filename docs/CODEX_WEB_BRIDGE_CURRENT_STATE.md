# Codex Web Bridge current state

Canonical handoff for `codex-web-bridge-v2`.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while routing model inference through UWA to logged-in ChatGPT Web. Codex remains authoritative for filesystem, shell, edits, tests, Git, sandbox and approval. CLI/protocol acceptance is necessary but does not replace the mandatory Desktop UI gate.

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
UWA reasoning-effort semantics documented            PASS
Codex Desktop UI live gate                           REQUIRED / pending
```

## P1.2 native remote V2 compaction: LIVE PASS

The valid macOS run used Codex CLI 0.153.4, the managed UWA provider, and the narrow Azure-name capability shim. The probe crossed the native auto-compaction threshold without crossing the hard effective context cap:

```text
AUTO_COMPACT_LIMIT=57600
HARD_CONTEXT_LIMIT=60800
PRE_TRIGGER_ACTIVE_TOKENS=57674
PRE_TRIGGER_OVER_HARD_CAP=NO
```

The trigger then produced the required remote-V2 evidence:

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

This closes the native remote-compaction trigger/protocol gate. Detailed record: `docs/CODEX_P1_REMOTE_V2_LIVE_PASS_2026-09-08.md`.

## Current gate: P1.2 same-thread post-remote recovery

P1.2 has one remaining correctness gate:

```text
remote V2 compact
→ continue the same Codex thread
→ do not search local rollout/session/history/private UWA stores
→ recover the original conversation-only synthetic token from compacted model-visible context
→ perform a real local write/read through Codex
→ exact checker PASS
```

After this passes, P1.2 closes.

## Accelerated main-merge path

The project is now release-focused. Broad P2-P5 feature expansion no longer blocks the first verified merge to `main` unless a remaining live gate exposes a dependency on it.

Merge-blocking sequence:

```text
M1 P1.2 same-thread post-remote recovery
M2 P1.3 minimal continuity blockers
   - lost-affinity/restart fallback correctness
   - stable identity / stale-generation fencing
   - uncertain tool-effect reconciliation before retry
M3 Desktop UI D1-D5
   - real Desktop local tool round trip
   - same-thread continuation
   - Desktop restart/history resume
   - Desktop + UWA restart recovery
   - clean official-account restore
   - Medium/High reasoning end-to-end verification folded into this gate
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

Decision: no architecture pivot. Official Codex remains the only local executor. Useful reliability ideas are tracked for P1.3/post-main hardening, but adjacent-project feature parity does not enter the current release-critical path.

Detailed review: `docs/EXTERNAL_CODING_BRIDGE_REVIEW_2026-09-08.md`.

## Repository provenance and post-main standalone extraction

The current GitHub repository is an actual fork of `lumingya/universal-web-api` and retains upstream AGPL-3.0 code/history. It also contains substantial newly implemented Codex Web Bridge code.

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
P1.2 same-thread post-remote recovery                CURRENT
P1.3 minimal continuity blockers                     pending
Desktop UI D1-D5 + Medium/High verification          pending / mandatory
real-project pilot                                   pending / mandatory
final regression/safety/docs                         pending / mandatory
post-main standalone repository extraction           planned
```

## Continuity layers

1. Codex Desktop / CLI thread history.
2. Private UWA Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Git-tracked handoff documents as long-term project truth.

## Collaboration / merge / safety

Every completed stage, important failure, repair and disruptive checkpoint is committed before moving on. README, this canonical state, progress tracking, stage/failure records and Draft PR stay aligned.

Do not merge into `main` until the accelerated merge-blocking sequence is green. P2-P5 enhancements continue after the first verified `main` baseline unless a remaining gate proves one is required earlier.

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, Codex memory workspace content, or private project source captured during acceptance.
