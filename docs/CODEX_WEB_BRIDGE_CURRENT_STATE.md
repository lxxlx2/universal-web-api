# Codex Web Bridge current state

Canonical handoff for `codex-web-bridge-v2`.

## Goal

Run official Codex Desktop / Codex CLI as the local coding agent while supporting a controlled UWA fallback to logged-in ChatGPT Web. Codex remains authoritative for filesystem, shell, edits, tests, Git, sandbox and approval. Provider/model/effort routing must be visible and auditable before long work starts.

The first release is intentionally narrow and release-focused. Broad framework expansion, generalized automatic routing, dashboards and unrelated upstream cleanup remain post-main unless a live release gate proves they are required.

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
P1.2 native remote V2 compaction macOS live          PASS
P1.2 same-thread post-remote recovery                 PASS / CLOSED
P1.3 minimal continuity blockers                     PASS / CLOSED
ChatGPT idle-composer send repair                     PASS / LIVE / CLOSED
Desktop D1-D5                                        PASS / LIVE / CLOSED
Hybrid H0-H5                                         PASS / LIVE / CLOSED
M3a Hybrid Routing Safety                            PASS / LIVE / CLOSED
M3b Desktop UI                                       PASS / LIVE / CLOSED
```

## M3a Hybrid Routing Safety closed

The full hybrid gate is now complete:

```text
H0 metadata-only route audit helper                   PASS / CLOSED
H1 provider/model/effort fail-closed guard            PASS / CLOSED
H2 fresh Desktop route probe                          PASS / LIVE / CLOSED
H3 explicit official -> UWA stateful handoff          PASS / LIVE / CLOSED
H4 private metadata-only transition ledger            PASS / CLOSED
H5 aggregate synthetic hybrid acceptance              PASS / CLOSED
```

The final H3 run preserved the official source effect exactly once, appended the UWA continuation effect exactly once, passed the independent handoff checker, emitted a real `exec_command` client tool call, proved `uwa / chatgpt / high`, excluded metadata-helper traffic from agent accounting, and ended with request-manager running count zero.

H4 writes only metadata and hashed identities to a private local ledger. H5 rechecked exact effect counts, route identity and no-duplicate behavior.

Detailed record: `docs/CODEX_HYBRID_M3A_LIVE_PASS_2026-09-10.md`.

## H3 blockers found and closed

```text
browser composer send false-positive                 CLOSED by 1dac853
required exec_command phrasing miss                   CLOSED by 38ede75
hidden Codex metadata-helper interference             CLOSED by de875e4
```

The browser repair was proven by direct High `response.completed`. The required-tool repair was proven by a genuine client `exec_command` round trip and `function_call_output`. The metadata helper is now classified before required-tool logic, answered locally, excluded from affinity/agent route accounting and does not consume the controlled ChatGPT Web coding lane.

## Current release-critical path

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       PASS / LIVE / CLOSED
M3b Desktop UI D1-D5                                  PASS / LIVE / CLOSED
M4 one real-project long-task pilot                   CURRENT
M5 final A-F + compaction + restart regression        pending
M6 CI green + public-repo safety + docs/license       pending
M7 inspect branch topology + merge V2 to main         pending
```

M4 deliberately uses this repository as the real project. The pilot must perform a non-trivial bounded code/test task through a fresh verified UWA Codex turn, prove real local tools and route metadata, leave request-manager clean, validate the resulting diff, and only then push the verified change.

A known release-hardening item is suitable for this pilot: ensure a backing `_run_chat_completion_final` task created by the streamed V2 attempt cannot survive cancellation/closure of the outer ASGI generator. The task must be cancelled and awaited without swallowing the caller's `CancelledError`, with regression coverage and no behavior change on normal completion.

## Post-main standalone plan

After verified V2 is merged to `main`:

```text
S1 dependency/import/runtime audit + core manifest
S2 create standalone attributed repository
S3 rerun full CI + CLI/Desktop/live parity acceptance
S4 publish first standalone research release
```

Preserve AGPL-3.0, copyright/license notices and explicit upstream attribution. Remove unrelated generic fork surface only after the verified `main` baseline exists.

## Reasoning effort

```text
UWA default                 high
request effort=medium       supported and page-verified
request effort=high         supported and page-verified
request effort=low/light    unsupported / fail closed
```

The actual Responses request plus verified ChatGPT Web state is authoritative. A visible Desktop slider alone is not execution proof.

## Collaboration and safety

Every completed live stage, important failure, repair and disruptive checkpoint is committed before moving on. Repository docs, README, progress tracking and the Draft PR should remain aligned with canonical state.

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, private hybrid handoff content, or captured tool bodies/output.
