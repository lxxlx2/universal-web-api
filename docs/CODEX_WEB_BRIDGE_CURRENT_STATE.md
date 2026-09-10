# Codex Web Bridge current state

Canonical handoff for `codex-web-bridge-v2`.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while supporting a controlled UWA fallback to logged-in ChatGPT Web. Codex remains authoritative for filesystem, shell, edits, tests, Git, sandbox and approval. Provider/model/effort routing must be visible and auditable before long work starts.

The first release is intentionally narrow and release-focused. Broad P2-P5 governance, generalized automatic routing, dashboards and unrelated upstream cleanup do not block the first verified merge to `main` unless a remaining live gate exposes a real dependency.

## Verified core

```text
Stage A-F protocol/CLI acceptance                    PASS
aggregate A-F checker                                PASS
Responses tool / call-id continuity                  PASS
P1.1 Responses compact direct live                   PASS
versioned UWA lifecycle/provider switch CI/live      PASS
P1.2 stream/usage compatibility                      PASS
P1.2 native auto-compact trigger/local fallback      PASS
P1.2 remote V2 protocol implementation/CI            PASS
P1.2 UWA provider precondition live                  PASS
P1.2 native remote V2 compaction macOS live          PASS
P1.2 same-thread post-remote recovery                 PASS / CLOSED
P1.3 lost-affinity/restart fallback                   PASS / CLOSED
P1.3 stable identity/stale fencing                    PASS / CLOSED
P1.3 uncertain tool-effect retry safety               PASS / CLOSED
Hybrid H0 metadata route audit                        PASS / CI
Hybrid H1 exact route/model/effort guard              PASS / CI
Hybrid H2 fresh Desktop route probe                   PASS / LIVE / CLOSED
ChatGPT idle-composer send repair                     PASS / LIVE / CLOSED
H3 required client-tool path                          PASS / LIVE / CLOSED
H3 metadata-helper isolation                          PASS / LIVE / CLOSED
Desktop D1 real local-tool round trip                 PASS / LIVE / CLOSED
Desktop D2 same-thread continuation                   PASS / LIVE / CLOSED
Desktop D3 Desktop restart + history resume           PASS / LIVE / CLOSED
Desktop D4 Desktop + UWA restart recovery             PASS / LIVE / CLOSED
Desktop D5 official restore + harmless task           PASS / LIVE / CLOSED
```

## Hybrid Routing Safety

A pre-D1 Desktop event proved that an already-existing Desktop conversation could resume through the official provider while UWA-backed sessions also existed. Local metadata distinguished the official execution from UWA sessions. Therefore top-level config and UI labels alone are insufficient proof of the route used by an existing Desktop thread.

Release-critical hybrid scope:

```text
H0 metadata-only route audit helper                   PASS
H1 explicit route intent + fail-closed quality floor  PASS
H2 tiny fresh-thread route probe                      PASS
H3 explicit official -> UWA stateful handoff          CURRENT; source PASS; blockers closed; final handoff acceptance next
H4 private metadata-only transition ledger            marker foundation present
H5 synthetic hybrid acceptance                        pending
```

No silent premium-quota spend and no silent quality downgrade are allowed. Unknown quota state must not be guessed. Route checks remain mandatory before long or real-project work.

Detailed design: `docs/CODEX_HYBRID_ROUTING_SAFETY_2026-09-08.md`.

## H3 blocker closure

The preserved synthetic official source state remains valid: the official task produced `OFFICIAL_EFFECT_ONCE` exactly once and was verified on `openai / gpt-6-astra / low` with UWA stopped.

During the UWA-side work, three independent blockers were found and closed:

```text
browser composer send false-positive                 CLOSED by 1dac853; direct High response.completed live-proven
required exec_command phrasing miss                   CLOSED by 38ede75; real client function call live-proven
hidden Codex metadata-helper interference             CLOSED by de875e4; local isolated helper live-proven
```

The required-tool live probe proved the real agent request declared `exec_command`, the detector selected it, a bounded repair emitted a genuine `exec_command` function call, Codex executed it locally and returned `function_call_output`, the final response completed, and request-manager running count returned to zero.

The metadata-helper live probe proved a current-Codex hidden thread-title shaped request is classified before required-tool logic. The helper completed locally with a bounded structured title, emitted no function call, touched no ChatGPT Web coding lane, left zero running requests, was traced as `metadata_helper`, and was ignored by agent-route audit counts.

Detailed records:

- `docs/CODEX_H3_REQUIRED_TOOL_REPAIR_LIVE_PASS_2026-09-10.md`
- `docs/CODEX_H3_METADATA_HELPER_ISOLATION_LIVE_PASS_2026-09-10.md`
- `docs/CODEX_H3_METADATA_HELPER_INTERFERENCE_2026-09-09.md`
- `docs/CODEX_DIRECT_HIGH_BROWSER_STALL_2026-09-09.md`

## Desktop UI live gate

```text
D1 real Desktop local tool round trip                 PASS / CLOSED
D2 same Desktop thread continuation                   PASS / CLOSED
D3 full Desktop app restart + history resume          PASS / CLOSED
D4 Desktop + UWA restart + same-thread recovery       PASS / CLOSED
D5 clean official-account restore + harmless task     PASS / LIVE / CLOSED
Desktop UI D1-D5                                      PASS / LIVE / CLOSED
```

D1-D4 prove real Desktop local tool execution, context continuity and restart recovery through `uwa / chatgpt / high`. D5 proves clean restoration to signed-in official Codex plus one harmless local-tool task on authoritative `openai / gpt-6-astra / low` metadata with UWA unavailable by design.

The synthetic D5 official workspace diff is intentionally preserved as H3 source state. The next gate must start a fresh UWA Codex agent turn in the same workspace, inspect durable state first, append `UWA_CONTINUATION_ONCE` exactly once, keep `OFFICIAL_EFFECT_ONCE` exactly once, pass the independent handoff checker, and prove `uwa / chatgpt / high` from authoritative agent-turn metadata and post-marker UWA wire activity.

## Current release-critical path

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       CURRENT; H0-H2 PASS, H3 final handoff acceptance next
M3b Desktop UI D1-D5                                  PASS / LIVE / CLOSED
M4 one real-project long-task pilot                   pending
M5 final A-F + compaction + restart regression        pending
M6 CI green + public-repo safety + docs/license       pending
M7 inspect branch topology + merge V2 to main         pending
```

After the verified V2 release candidate is merged to `main`, create the clearer standalone repository by dependency-auditing and extracting the bridge core plus genuinely required upstream runtime:

```text
S1 dependency/import/runtime audit + core manifest
S2 create standalone attributed repository
S3 full CI/live parity acceptance
S4 first standalone research release
```

Preserve AGPL-3.0, copyright/license notices and explicit upstream attribution. Remove unrelated generic fork surface only after the verified `main` baseline exists.

Detailed plan: `docs/POST_MAIN_STANDALONE_REPOSITORY_PLAN_2026-09-08.md`.

## Reasoning effort

```text
UWA default                 high
request effort=medium       supported and page-verified
request effort=high         supported and page-verified
request effort=low/light    unsupported / fail closed
```

The actual Responses request plus verified ChatGPT Web state is authoritative. A visible Desktop slider position alone is not accepted as proof.

## Collaboration and safety

Every completed live stage, important failure, repair and disruptive checkpoint is committed before moving on. README, this canonical state, progress tracking, Desktop acceptance and the Draft PR should stay aligned as closely as practical.

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, Codex memory workspace content, local hybrid handoff prompts, or private project source captured during acceptance.
