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
Desktop D5 official restore lifecycle     PASS / LIVE / CLOSED
Desktop D5 harmless official task         PASS / LIVE / CLOSED
Desktop gate overall                      PASS / LIVE / CLOSED
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

## D5: restore normal official-account mode and model selection — PASS

Goal: prove the project can be exited cleanly and normal Codex Desktop account usage is restored without pinning a model.

Normal procedure is one command:

```bash
cd ~/universal-web-api
python3 tools/codex_provider_switch.py official
```

The first D5 live run restored Memories and account-default provider/model/reasoning configuration, preserved authentication and removed the private UWA restore state. It also exposed a real lifecycle defect: the old provider-switch stop path terminated the active `main.py` listener while leaving the repository-owned `start.py` launcher alive, so a fresh healthy TCP 8199 listener respawned immediately.

Commit `143b396` repaired that defect by routing the provider-switch stop path through the hardened launcher-aware `codex_uwa_lifecycle.stop_uwa()` implementation. Focused provider-switch/lifecycle coverage passes 18/18 and the corresponding Security hardening GitHub Actions run succeeded.

The repaired live rerun then passed the shutdown and no-respawn gate. At T+0, T+3, T+10 and T+20 seconds, metadata-only checks all observed zero repository-owned `start.py`, zero repository-owned `main.py`, zero TCP 8199 listeners and no UWA pidfile. The lifecycle helper reported `STATUS=STOPPED`. Provider status remained at signed-in account defaults with `UWA_RESTORE_STATE=ABSENT`, and the repository working tree remained clean.

After official Codex allowance became available, a fresh actual Codex Desktop conversation completed a bounded synthetic local task through the restored official route. The signed-in account model picker exposed GPT-6 Astra; the bounded task used the Light reasoning tier. Independent checker evidence proved exactly one local source effect:

```text
OFFICIAL_EFFECT_COUNT=1
OFFICIAL_SOURCE_PASS
```

Metadata-only route audit reported:

```text
latest session provider = openai
latest session model = gpt-6-astra
latest session effort = low
UWA health = unavailable
post-marker UWA requests = 0
post-marker UWA responses = 0
provider=openai route expectation = PASS
```

This proves the successful Desktop task used the restored official provider while UWA remained stopped. The selected account-controlled model and reasoning tier were reflected in authoritative local session metadata.

Detailed records:

- `docs/CODEX_DESKTOP_D5_OFFICIAL_UWA_RESPAWN_FAILURE_2026-09-09.md`
- `docs/CODEX_DESKTOP_D5_LIFECYCLE_RERUN_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_D5_LIVE_PASS_2026-09-09.md`

Do not record account identifiers or usage amounts in the public repository.

## Final Desktop gate

Desktop UI D1-D5 is PASS / LIVE / CLOSED. The final merge gate still requires Hybrid Routing Safety H3-H5, the real-project pilot, final regressions, CI/public-repo safety checks and branch-topology inspection before merge to `main`.
