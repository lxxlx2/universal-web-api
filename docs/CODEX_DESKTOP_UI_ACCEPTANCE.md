# Codex Desktop UI live acceptance

This gate exists because protocol/CLI acceptance and actual Desktop usage are not identical evidence.

Stage A-F already prove the core Responses bridge, client-side tool execution, same-thread continuity, long-running stdin handling and UWA restart recovery. The final Stage E/F runs were machine-audited primarily through `codex exec` / `codex exec resume`, so those results must not be presented as completed Desktop UI validation.

The production target includes normal use from ChatGPT Desktop in **Codex mode** on macOS. This document defines the additional live gate required before merge to `main`.

## Status

```text
CLI / protocol A-F acceptance             PASS
aggregate A-F checker                     PASS
P1.1 compact live                         PASS
versioned UWA lifecycle CI                PASS
Desktop D1 tool round trip                PASS / LIVE / CLOSED
Desktop D2 same-thread continuation       PASS / LIVE / CLOSED
Desktop D3 Desktop app restart resume     PASS / LIVE / CLOSED
Desktop D4 Desktop + UWA restart resume   PASS / LIVE / CLOSED
Desktop D5 official-account switch        READY / CURRENT
Desktop gate overall                      REQUIRED BEFORE MAIN MERGE
```

## Safety

Use only `~/uwa-codex-acceptance` for D1-D4. Do not point these first Desktop runs at a private/production repository.

A Desktop case is PASS only when both are true:

1. the action is performed from the actual ChatGPT Desktop Codex UI;
2. a machine-auditable local artifact/checker confirms the expected result.

Assistant prose or screenshots alone are insufficient.

## D1: Desktop native tool round trip — PASS

Goal: prove that an actual Desktop Codex chat opened on the acceptance workspace can call a real local tool and complete a small coding task through UWA.

Verified live result:

```text
multi_file: PASS
ACCEPTANCE_PASS
route = uwa / chatgpt / high
real exec_command function calls = YES
completed Responses turn = YES
test files modified = NO
```

The actual Desktop UI modified only `multi_file/math_ops.py` and `multi_file/summary.py`, ran the real unittest suite, and passed the independent checker. Metadata-only wire traces proved three `exec_command` function calls and a completed Responses turn.

Detailed record: `docs/CODEX_DESKTOP_D1_LIVE_PASS_2026-09-08.md`.

## D2: Desktop same-thread continuation — PASS

Goal: prove that conversation context survives across two turns inside the actual Desktop thread.

Verified live result:

```text
first turn                     CONTEXT_READY
second turn                    CONTEXT_PASS
independent checker            context: PASS / ACCEPTANCE_PASS
route                          uwa / chatgpt / high
post-marker UWA requests       3
post-marker UWA responses      3
route expectation              PASS
```

The second turn stayed in the same Desktop conversation, did not manually repeat the acceptance token, executed a real local command, created and read the expected `context/result.txt`, and passed the independent checker.

Detailed record: `docs/CODEX_DESKTOP_D2_LIVE_PASS_2026-09-09.md`.

## D3: Desktop application restart resume — PASS

Goal: prove Desktop history can restore the same Codex thread after the desktop application itself exits.

Verified live result:

```text
independent checker                         context: PASS / ACCEPTANCE_PASS
route                                       uwa / chatgpt / high
session identity before/after app restart   MATCH
post-marker UWA requests                    3
post-marker UWA responses                   3
latest UWA status                           completed
route expectation                           PASS
```

The actual Desktop application was exited and reopened, the same history thread was resumed, and the second turn recovered the conversation-only acceptance context and passed the local checker. Real thread/session identifiers and process identifiers are intentionally excluded from the public record.

Detailed record: `docs/CODEX_DESKTOP_D3_LIVE_PASS_2026-09-09.md`.

## D4: Desktop + UWA restart resume — PASS

Goal: reproduce Stage F through the actual Desktop UI using the versioned lifecycle path.

Verified live result:

```text
independent checker                     context: PASS / ACCEPTANCE_PASS
session identity before/after boundary MATCH
route                                  uwa / chatgpt / high
post-marker UWA requests               3
post-marker UWA responses              3
real exec_command present              YES
completed Responses turn               YES
route expectation                      PASS
```

The installed `codex-uwa*` commands are the thin wrappers produced by `tools/install_codex_uwa_commands.py`. The versioned lifecycle helper is fail-closed: stop does not succeed until TCP 8199 is empty, restart requires a healthy owned listener, and restart rejects reused listener PIDs. After the Desktop and UWA process boundaries, the same Desktop history thread recovered the hidden context, executed real local tools and passed the independent checker.

Detailed record: `docs/CODEX_DESKTOP_D4_LIVE_PASS_2026-09-09.md`.

## D5: restore normal official-account mode and model selection

Goal: prove the project can be exited cleanly and normal Codex Desktop account usage is restored without pinning a model.

Normal procedure is one command:

```bash
cd ~/universal-web-api
python3 tools/codex_provider_switch.py official
```

The command automatically quits Desktop, stops the verified UWA listener, restores saved Memories settings, removes only top-level provider/model/reasoning pins, preserves authentication and the UWA provider definition, and reopens Desktop.

In Codex mode verify:

1. UWA is not required for the session;
2. the model picker is controlled by the signed-in account/workspace rather than a README/CLI hard-coded model;
3. any currently available model can be selected, including Astra when the account/rollout permits it;
4. a harmless local Codex task can run successfully when official quota is available.

A quota-limit response after a clean official restore is not a bridge-routing failure. If official quota is exhausted, record the clean restore separately and complete the harmless-task proof after the official allowance resets.

Do not record account identifiers or usage amounts in the public repository.

## Final Desktop gate

Desktop UI overall becomes PASS only after D1-D5 are recorded with non-sensitive evidence. The final merge gate requires this document, README, canonical state, progress tracking and the Draft PR to agree on the same result.
