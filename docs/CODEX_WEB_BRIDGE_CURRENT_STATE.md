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

## Current gate: M4 focused cancellation repair

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

The deterministic recovery path passed environment/preflight handling and isolated the remaining work to focused async-stream cancellation regressions.

The first focused diagnostic found one real cleanup-ordering issue and one overconstrained transport assertion. The implementation was then changed so unwind clears the workflow reuse hint before cancelling/awaiting an unfinished backing task.

The latest rerun still reported two failures, but both failed before reaching any cancellation assertion. Both tests required their first yielded chunk to contain `response.created`, while the observed first chunk was `response.in_progress`. Normal completion still passed.

Current interpretation:

```text
production cleanup ordering                         prepared
normal completion regression                        PASS
consumer-cancellation lifecycle assertion            not reached
explicit aclose lifecycle assertion                  not reached
latest blocker                                      test-only preamble event assumption
```

`tools/codex_m4_focused_repair_and_close.py` is now updated so the lifecycle tests do not depend on a specific initial Responses event spelling. Consumer cancellation now ignores the preamble chunk and validates cancellation propagation, backing-task cleanup and final reuse-hint state. The `aclose()` test ignores the preamble, requires only a non-empty progress chunk, then validates backing-task cleanup and final reuse-hint state.

The remaining closure flow is still fail-closed: three focused stdlib regressions, `py_compile`, `git diff --check`, one bounded read-only Codex/UWA review, authoritative `uwa / chatgpt / high` verification, request-manager cleanup, and commit/push of only the implementation and regression-test paths.

Do not rerun the original 12-minute long task.

Current records:

- `docs/CODEX_M4_LONG_TASK_TIMEOUT_RECOVERY_2026-09-10.md`
- `docs/CODEX_M4_FOCUSED_UNITTEST_FAILURE_2026-09-10.md`
- `docs/CODEX_M4_FOCUSED_REPAIR_2026-09-10.md`
- `docs/CODEX_M4_EVENT_ASSUMPTION_REPAIR_2026-09-10.md`

## Current release-critical path

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       PASS / LIVE / CLOSED
M3b Desktop UI D1-D5                                  PASS / LIVE / CLOSED
M4 one real-project long-task pilot                   CURRENT / focused cancellation repair
M5 final A-F + compaction + restart regression        pending
M6 CI green + public-repo safety + docs/license       pending
M7 inspect branch topology + merge V2 to main         pending
```

M4 closes only after the focused closer reports `M4_REAL_PROJECT_LONG_TASK_PILOT=PASS_LIVE_CLOSED`.

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

Every completed live stage, important failure, repair and disruptive checkpoint is committed before moving on. Repository docs, README, progress tracking and Draft PR should remain aligned with canonical state.

Never commit browser profiles, cookies, local storage, credentials, private logs, full wire traces, Responses SQLite contents, live thread/process/browser identifiers, private hybrid handoff content, or captured tool bodies/output.

## Latest M4 checkpoint — completed bounded review

The next focused rerun passed all three lifecycle regressions and reached the bounded Codex/UWA review successfully:

```text
focused cancellation regressions          PASS 3/3
py_compile                                PASS
git diff --check                          PASS
bounded Codex review RC                   0
review event flow                         thread.started -> turn.started -> item.started/item.completed -> turn.completed
real local tool activity                  YES
transport stderr errors                   NONE
model-authored text marker                absent
```

The missing `M4_RECOVERY_REVIEW_OK` marker is now treated as a non-authoritative presentation assertion. The stronger acceptance evidence is a completed Codex turn plus real tool execution, post-marker `agent_turn` wire metadata, completed response metadata, exact `uwa / chatgpt / high` route proof, and a clean request-manager/browser postcondition.

`tools/codex_m4_finalize_completed_review.py` performs that structural close without repeating the already-completed Web review. It reruns only the deterministic local regression checks, validates post-marker structural evidence and health, then commits/pushes the two expected M4 paths if every gate passes.

Additional record: `docs/CODEX_M4_COMPLETED_REVIEW_STRUCTURAL_GATE_2026-09-10.md`.

## Latest M4 checkpoint — multi-source real-tool proof

The first structural finalizer rerun kept all deterministic validation green and found one post-marker `agent_turn` response with `chatgpt / high` and `response_status=completed`, but its response summary contained no `exec_command` name. The earlier bounded Codex CLI review had already emitted a command-execution start/completion pair and `turn.completed`, so the remaining mismatch is confined to one observability field.

`tools/codex_m4_finalize_completed_review_v2.py` now closes that gap without repeating the Web review. It keeps the response-summary proof when available and adds two independent metadata-only fallbacks: a post-marker Responses `function_call_output`, or a post-marker Codex rollout command/function-call event. It still requires post-marker `agent_turn` traffic, `chatgpt / high`, a completed response, the authoritative `uwa / chatgpt / high` route audit, clean UWA health, and the three focused regressions before commit/push.

The new scanner requires event timestamps and never prints command bodies, tool output, prompts, raw thread ids, rollout paths, cookies or credentials. M4 remains CURRENT until this finalizer reports `M4_REAL_PROJECT_LONG_TASK_PILOT=PASS_LIVE_CLOSED`.

## M4 closed — M5 is current

The multi-source finalizer completed successfully on 2026-09-10. The accepted implementation commit is `38554bd9d2301783d1bc2d9aff8005c60c70f389` and changes only `app/api/codex_responses_v2.py` plus `tests/test_codex_v2_stream_cancellation.py`.

Final M4 evidence:

```text
focused cancellation regressions                 PASS 3/3
py_compile                                       PASS
git diff --check                                 PASS
post-marker agent request/response               present
post-marker chatgpt/high route                    PASS
Responses function_call_output proof             present
Codex rollout command-event proof                present
completed response                               present
authoritative route audit                        uwa / chatgpt / high PASS
final request-manager running count              0
final browser connection                         healthy
commit + push                                    PASS
```

The model-authored text marker is not part of the authoritative gate. Real client-tool execution is proven independently by a returned `function_call_output` and a timestamped Codex command-execution event.

M4 is now `PASS / LIVE / CLOSED`. M5 is `CURRENT` and owns the final aggregate A-F, compaction/continuity regression, and fresh post-restart runtime smoke before M6.

Detailed record: `docs/CODEX_M4_REAL_PROJECT_LONG_TASK_LIVE_PASS_2026-09-10.md`.

Updated release-critical state:

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       PASS / LIVE / CLOSED
M3b Desktop UI D1-D5                                  PASS / LIVE / CLOSED
M4 one real-project long-task pilot                   PASS / LIVE / CLOSED
M5 final A-F + compaction + restart regression        CURRENT
M6 CI green + public-repo safety + docs/license       pending
M7 inspect branch topology + merge V2 to main         pending
```

## M5 closed — M6 is current

The final M5 safe-v2 run completed successfully on 2026-09-10. It used a fresh private deterministic Stage A-F replay, kept the historical live workspace untouched, ran the complete current Codex regression family, restarted UWA twice, and resumed the same Codex thread through the second restart.

Final M5 evidence:

```text
Stage A-F deterministic replay                    PASS
current Codex test files                           37
Codex regression                                   201 passed / 0 failed
py_compile                                         PASS
git diff --check                                  PASS
first UWA restart                                  PASS
seed turn                                          PASS
second UWA restart                                 PASS
same Codex thread after restart                    YES
real local client tool activity                    YES
continuity result exact                            YES
post-marker agent request/response                 5 / 5
post-marker latest status                          completed
authoritative route                                uwa / chatgpt / high
final request-manager running count                0
final browser connection                           healthy
repository clean                                   YES
private workspace cleanup                          PASS
```

M5 is `PASS / LIVE / CLOSED`. M6 is `CURRENT` and owns final CI, public-repository safety, documentation, provenance and license review. M7 remains pending until M6 closes.

M5 live record: `docs/CODEX_M5_FINAL_REGRESSION_LIVE_PASS_2026-09-10.md`.
M6 audit: `docs/CODEX_M6_RELEASE_SAFETY_AUDIT_2026-09-10.md`.

Current release-critical state:

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       PASS / LIVE / CLOSED
M3b Desktop UI D1-D5                                  PASS / LIVE / CLOSED
M4 one real-project long-task pilot                   PASS / LIVE / CLOSED
M5 final A-F + compaction + restart regression        PASS / LIVE / CLOSED
M6 CI green + public-repo safety + docs/license       CURRENT
M7 inspect branch topology + merge V2 to main         pending
```

## M6 closed — M7 is current

M6 release safety review completed on 2026-09-10. The documentation head passed the Security hardening workflow, including public-repository safety, Ubuntu/macOS security matrices and upstream regression. GitHub repository metadata still identifies the project as a public fork of `lumingya/universal-web-api` under AGPL-3.0. `LICENSE`, `SECURITY.md`, `docs/REFERENCES_AND_ATTRIBUTION.md`, the Chinese README and the Codex-specific English README all retain the required release-facing safety and provenance information.

No workflow artifacts containing runtime state were published by the reviewed CI run. No new product behavior was added during M6.

M6 is `PASS / CLOSED`. M7 is `CURRENT` and owns final branch-topology inspection and merge of the verified V2 branch into `main`.

M6 record: `docs/CODEX_M6_RELEASE_SAFETY_AUDIT_2026-09-10.md`.

Current release-critical state:

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       PASS / LIVE / CLOSED
M3b Desktop UI D1-D5                                  PASS / LIVE / CLOSED
M4 one real-project long-task pilot                   PASS / LIVE / CLOSED
M5 final A-F + compaction + restart regression        PASS / LIVE / CLOSED
M6 CI green + public-repo safety + docs/license       PASS / CLOSED
M7 inspect branch topology + merge V2 to main         CURRENT
```
