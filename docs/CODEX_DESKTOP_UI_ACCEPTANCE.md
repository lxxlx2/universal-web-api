# Codex Desktop UI live acceptance

This gate exists because protocol/CLI acceptance and actual Desktop usage are not identical evidence.

Stage A-F already prove the core Responses bridge, client-side tool execution, same-thread continuity, long-running stdin handling and UWA restart recovery. The final Stage E/F runs were machine-audited primarily through `codex exec` / `codex exec resume`, so those results must not be presented as completed Desktop UI validation.

The production target includes normal use from ChatGPT Desktop in **Codex mode** on macOS. This document defines the additional live gate required before merge to `main`.

## Status

```text
CLI / protocol A-F acceptance             PASS
aggregate A-F checker                     PASS
Desktop D1 tool round trip                pending
Desktop D2 same-thread continuation       pending
Desktop D3 Desktop app restart resume     pending
Desktop D4 Desktop + UWA restart resume   pending
Desktop D5 official-account switch        pending
Desktop gate overall                      REQUIRED BEFORE MAIN MERGE
```

## Safety

Use only `~/uwa-codex-acceptance` for D1-D4. Do not point these first Desktop runs at a private/production repository.

A Desktop case is PASS only when both are true:

1. the action is performed from the actual ChatGPT Desktop Codex UI;
2. a machine-auditable local artifact/checker confirms the expected result.

Assistant prose or screenshots alone are insufficient.

## D1: Desktop native tool round trip

Goal: prove that an actual Desktop Codex chat opened on the acceptance workspace can call a real local tool and complete a small coding task through UWA.

Procedure:

```bash
cd ~/universal-web-api
python3 tools/codex_desktop_acceptance.py prepare --scenario multi_file
python3 tools/codex_desktop_acceptance.py preflight --scenario multi_file
python3 tools/codex_desktop_acceptance.py prompts --scenario multi_file
```

Then in ChatGPT Desktop:

1. select Codex;
2. open `~/uwa-codex-acceptance`;
3. start a fresh Codex chat;
4. send the generated `multi_file` prompt;
5. allow the task to finish;
6. run the checker in Terminal:

```bash
cd ~/universal-web-api
python3 tools/codex_desktop_acceptance.py check --scenario multi_file
```

PASS requires `multi_file: PASS` and real local command/edit evidence.

## D2: Desktop same-thread continuation

Goal: prove that conversation context survives across two turns inside the actual Desktop thread.

Procedure:

```bash
cd ~/universal-web-api
python3 tools/codex_desktop_acceptance.py prepare --scenario context
python3 tools/codex_desktop_acceptance.py preflight --scenario context
python3 tools/codex_desktop_acceptance.py prompts --scenario context_1
python3 tools/codex_desktop_acceptance.py prompts --scenario context_2
```

In one Desktop Codex chat:

1. send `context_1` and require `CONTEXT_READY`;
2. do not repeat the hidden token manually;
3. send `context_2` in the same Desktop thread;
4. require real local execution and `CONTEXT_PASS`;
5. run:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario context
```

PASS requires the exact expected artifact and `ACCEPTANCE_PASS`.

## D3: Desktop application restart resume

Goal: prove Desktop history can restore the same Codex thread after the desktop application itself exits.

Procedure:

1. prepare the `context` scenario;
2. in a fresh Desktop Codex thread send `context_1` and receive `CONTEXT_READY`;
3. fully quit ChatGPT Desktop;
4. reopen ChatGPT Desktop;
5. select Codex and reopen the exact same thread from history;
6. send `context_2` without repeating the token;
7. run the context checker.

PASS requires `CONTEXT_PASS` plus `ACCEPTANCE_PASS` after a real application restart.

## D4: Desktop + UWA restart resume

Goal: reproduce Stage F through the actual Desktop UI.

Procedure:

1. prepare fresh `context` fixture;
2. start a fresh Desktop Codex thread and send `context_1`;
3. receive `CONTEXT_READY` and verify `context/result.txt` is absent;
4. fully quit ChatGPT Desktop;
5. stop UWA and verify port 8199 has no listener;
6. restart UWA and verify `/health` is healthy and `/v1/codex/web-affinity` starts with zero bindings;
7. reopen ChatGPT Desktop;
8. reopen the same Desktop Codex thread from history;
9. send `context_2` without repeating the token;
10. verify the local artifact and run the checker.

PASS requires successful same-thread recovery across both process boundaries and `ACCEPTANCE_PASS`.

## D5: restore normal official-account mode and model selection

Goal: prove the project can be exited cleanly and normal Codex Desktop account usage is restored without pinning a model.

Procedure:

```bash
cd ~/universal-web-api
codex-uwa-stop
python3 tools/codex_provider_switch.py official
python3 tools/codex_uwa_memory_guard.py restore
python3 tools/codex_provider_switch.py status
```

Then fully quit/reopen ChatGPT Desktop. If prompted, sign in with the user's normal ChatGPT account. In Codex mode verify:

1. UWA is not required for the session;
2. the model picker is controlled by the signed-in account/workspace rather than a README/CLI hard-coded model;
3. any currently available model can be selected, including Astra when the account/rollout permits it;
4. a harmless local Codex task can run successfully.

Do not record account identifiers or usage amounts in the public repository.

## Final Desktop gate

Desktop UI overall becomes PASS only after D1-D5 are recorded with non-sensitive evidence. The final merge gate requires this document, README, canonical state, progress tracking and the Draft PR to agree on the same result.
