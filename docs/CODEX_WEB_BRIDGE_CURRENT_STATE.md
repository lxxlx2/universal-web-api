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

The full hybrid gate is complete:

```text
H0 metadata-only route audit helper                   PASS / CLOSED
H1 provider/model/effort fail-closed guard            PASS / CLOSED
H2 fresh Desktop route probe                          PASS / LIVE / CLOSED
H3 explicit official -> UWA stateful handoff          PASS / LIVE / CLOSED
H4 private metadata-only transition ledger            PASS / CLOSED
H5 aggregate synthetic hybrid acceptance              PASS / CLOSED
```

The final H3 run preserved the official source effect exactly once, appended the UWA continuation effect exactly once, passed the independent handoff checker, emitted a real `exec_command` client tool call, proved `uwa / chatgpt / high`, excluded metadata-helper traffic from agent accounting, and ended with request-manager running count zero.

Detailed record: `docs/CODEX_HYBRID_M3A_LIVE_PASS_2026-09-10.md`.

## Current gate: M4 recovery

M4 uses this repository itself as the real project. The first long Codex/UWA turn passed route and health preconditions and performed substantial local tool activity, but the harness reached its 720-second wall-clock limit before `turn.completed`.

Safe observed metadata:

```text
configured route                         uwa / chatgpt / high
Codex elapsed                            719 seconds
real tool item count                     14
stream disconnect                        absent
workspace after timeout                  only app/api/codex_responses_v2.py modified
request-manager after                    0
browser after                            connected
```

The controlled Web turn visibly continued issuing real `exec_command` calls and was still probing Python/runtime candidates near the timeout. This is recorded as a bounded completion failure, not a transport disconnect or leaked UWA request.

Do not discard the partial workspace and do not rerun another unconstrained 12-minute coding turn. Current recovery runner:

```text
tools/codex_m4_resume_after_timeout.py
```

It accepts only the expected M4 dirty scope, rebuilds the intended stream-cancellation cleanup from tracked base, writes stdlib regression coverage, validates outside the Codex sandbox, runs one bounded read-only Codex/UWA validation turn with a required real `exec_command`, verifies `turn.completed`, `uwa / chatgpt / high`, and request-manager cleanup, then commits/pushes only the two expected code/test paths.

Detailed record: `docs/CODEX_M4_LONG_TASK_TIMEOUT_RECOVERY_2026-09-10.md`.

## Current release-critical path

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       PASS / LIVE / CLOSED
M3b Desktop UI D1-D5                                  PASS / LIVE / CLOSED
M4 one real-project long-task pilot                   CURRENT / recovery after bounded timeout
M5 final A-F + compaction + restart regression        pending
M6 CI green + public-repo safety + docs/license       pending
M7 inspect branch topology + merge V2 to main         pending
```

M4 closes only after the recovery runner reports `M4_REAL_PROJECT_LONG_TASK_PILOT=PASS_LIVE_CLOSED`.

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

Every completed live stage, important failure, repair and disruptive checkpoint is committed before moving on. Repository docs, README, progress tracking and Draft PR #2 should remain aligned with canonical state.

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, private hybrid handoff content, or captured tool bodies/output.
