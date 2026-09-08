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
Desktop D1 real local-tool round trip                 PASS / LIVE / CLOSED
Desktop D2 same-thread continuation                   PASS / LIVE / CLOSED
Desktop D3 Desktop restart + history resume           PASS / LIVE / CLOSED
Desktop D4 Desktop + UWA restart recovery             PASS / LIVE / CLOSED
D5 lifecycle code repair                              PASS / focused tests / CI
D5 repaired official lifecycle rerun                  PASS / LIVE
```

Detailed historical evidence remains in the dedicated `docs/CODEX_*` live/closure records.

## Hybrid Routing Safety

A pre-D1 Desktop event proved that an already-existing Desktop conversation could resume through the official provider while UWA-backed sessions also existed. Local metadata distinguished the official execution from UWA sessions. Therefore top-level config and UI labels alone are insufficient proof of the route used by an existing Desktop thread.

Release-critical hybrid scope:

```text
H0 metadata-only route audit helper                   PASS
H1 explicit route intent + fail-closed quality floor  PASS
H2 tiny fresh-thread route probe                      PASS
H3 explicit official -> UWA stateful handoff          pending
H4 private metadata-only transition ledger            marker foundation present
H5 synthetic hybrid acceptance                        pending
```

No silent premium-quota spend and no silent quality downgrade are allowed. Unknown quota state must not be guessed. Route checks remain mandatory before long or real-project work.

Detailed design: `docs/CODEX_HYBRID_ROUTING_SAFETY_2026-09-08.md`.

## Desktop UI live gate

```text
D1 real Desktop local tool round trip                 PASS / CLOSED
D2 same Desktop thread continuation                   PASS / CLOSED
D3 full Desktop app restart + history resume          PASS / CLOSED
D4 Desktop + UWA restart + same-thread recovery       PASS / CLOSED
D5 official restore lifecycle                         PASS / LIVE
D5 harmless real official-provider request            pending quota availability
Medium/High request -> ChatGPT Web verification      folded into Desktop gate
```

D1 proved real Desktop local execution/edit/test through `uwa / chatgpt / high` with metadata-only `exec_command` function-call evidence.

D2 proved two-turn context continuity in the same actual Desktop conversation with `CONTEXT_READY`, `CONTEXT_PASS`, independent `ACCEPTANCE_PASS`, and exact UWA route verification.

D3 proved Desktop history recovery after a full app exit/reopen. The same session identity was observed before and after restart, the context checker passed, and the resumed turn remained on `uwa / chatgpt / high` with three post-marker UWA request/response pairs and exact route expectation PASS.

D4 proved recovery across both Desktop and UWA process boundaries. The same Desktop session identity survived the double restart, the context checker passed, the post-restart route remained `uwa / chatgpt / high`, and metadata-only traces proved real `exec_command` calls plus a completed Responses turn.

D5 exposed a confirmed lifecycle blocker. The first official restore correctly restored Memories and account-default model/provider/reasoning configuration, preserved authentication and removed the private restore state, but the old provider-switch stop path killed only the active `main.py` listener while leaving the repository-owned `start.py` launcher alive. The launcher immediately recreated a healthy TCP 8199 listener.

Commit `143b396` repairs the defect by delegating provider-switch shutdown to the hardened launcher-aware `codex_uwa_lifecycle.stop_uwa()` path. Focused provider-switch/lifecycle regression coverage passes with 18 tests, and the Security hardening GitHub Actions run for `143b396` succeeded.

The repaired live D5 lifecycle rerun then passed. Metadata-only checks at T+0, T+3, T+10 and T+20 all showed zero repository-owned `start.py`, zero repository-owned `main.py`, zero TCP 8199 listeners and no UWA pidfile. The lifecycle helper reported `STATUS=STOPPED`, and provider status remained at account defaults with no private UWA restore state. This closes the respawn defect at the lifecycle level.

The only remaining D5 item is a harmless real official-provider request after restore when official Codex quota is available.

Detailed records:

- `docs/CODEX_DESKTOP_D1_LIVE_PASS_2026-09-08.md`
- `docs/CODEX_DESKTOP_D2_LIVE_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_D3_LIVE_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_D4_LIVE_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_D5_OFFICIAL_UWA_RESPAWN_FAILURE_2026-09-09.md`
- `docs/CODEX_DESKTOP_D5_LIFECYCLE_RERUN_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`

## Current release-critical path

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       CURRENT; H0-H2 PASS
M3b Desktop UI D1-D5                                  CURRENT; lifecycle PASS, final official request pending
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

## Continuity layers

1. Codex Desktop / CLI thread history.
2. UWA private Responses persistence at `~/.uwa/codex_responses.sqlite3`.
3. Process-local ChatGPT web-session / call-id affinity.
4. Local-only hybrid handoff/route metadata under `~/.uwa`.
5. Git-tracked handoff documents as long-term project truth.

## Collaboration and safety

Every completed live stage, important failure, repair and disruptive checkpoint is committed before moving on. README, this canonical state, progress tracking, Desktop acceptance and the Draft PR should stay aligned as closely as practical.

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, Codex memory workspace content, local hybrid handoff prompts, or private project source captured during acceptance.
