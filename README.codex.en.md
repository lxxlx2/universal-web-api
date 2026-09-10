# UWA Codex Web Bridge V2

English overview for the Codex-specific V2 work on this repository.

For the canonical live state and detailed release progress, see:

- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`

The existing `README.md` remains the primary Chinese project README. The existing `README.en.md` documents the broader upstream-style Universal Web API project; this file focuses specifically on the Codex Web Bridge V2 integration.

## What this project does

UWA Codex Web Bridge V2 keeps the official Codex Desktop / Codex CLI as the local execution authority while allowing model reasoning to be routed through a local UWA service to a logged-in ChatGPT Web session.

The separation of responsibilities is intentional:

```text
Codex Desktop / CLI
  owns local workspace, shell, edits, tests, Git, sandbox and approvals

UWA Codex Responses bridge
  translates and maintains the Responses protocol, route metadata and continuity

ChatGPT Web
  provides the model reasoning used by the controlled UWA route
```

The browser page itself does not receive direct filesystem authority. Local operations are still executed by the Codex client under its own sandbox and approval policy.

## Current release-critical status

As of 2026-09-10:

```text
Stage A-F protocol / CLI acceptance                 PASS
aggregate A-F checker                               PASS
real exec_command / function_call round trip        PASS
same-thread and restart continuity                  PASS
P1.1 compact compatibility                          PASS
P1.2 native auto-compact + remote V2 compaction     PASS / LIVE
P1.2 post-remote same-thread recovery               PASS / CLOSED
P1.3 continuity blockers                            PASS / CLOSED
ChatGPT idle-composer send repair                   PASS / LIVE / CLOSED
Hybrid H0-H5                                        PASS / LIVE / CLOSED
M3a Hybrid Routing Safety                           PASS / LIVE / CLOSED
Desktop D1-D5                                       PASS / LIVE / CLOSED
M3b Desktop UI                                      PASS / LIVE / CLOSED
M4 real-project long-task pilot                     PASS / LIVE / CLOSED
remote-compaction cancellation follow-up            PASS / CI
M5 final regression                                 CURRENT
M6 CI / public safety / docs / provenance           pending
M7 merge verified V2 to main                        pending
```

M4 is closed. The accepted implementation passed all three focused cancellation regressions, a bounded real Codex/UWA review, multi-source real client-tool proof, authoritative `uwa / chatgpt / high` route verification, and final request-manager/browser health checks.

A 2026-09-10 reference-project compatibility scan found one separate release-critical lifecycle hole in native remote compaction. That path now applies the same pending-worker cancel-and-await discipline on generator unwind, keeps normal completion unchanged, adds cancellation/`aclose()` regression coverage, and tightens compact-summary guidance so completed historical requests are not revived as current actionable goals. Security hardening CI for that follow-up passed.

M5 is the current gate. Its first live attempt stopped before any correctness regression because the original validation probe required the runtime Python to import the development-only `pytest` package. Production `requirements.txt` intentionally does not include pytest. This is classified as a harness/environment precondition issue, not a product regression.

The safe M5 runner now selects a Python that can import the UWA/Codex runtime first. If pytest is absent, it bootstraps pytest only into private `~/.uwa` validation state and leaves the repository and production requirements untouched. Security hardening CI for this safe bootstrap passed.

Current one-shot runner:

```text
tools/codex_m5_final_regression_safe.py
```

M5 still rechecks Stage A-F, the complete current `test_codex_*.py` regression family, current-code UWA restart, and a same-thread continuity smoke across a real UWA restart without using the official provider.

## Quick start

Update the active V2 branch and install the local helper commands:

```bash
cd ~/universal-web-api
git switch codex-web-bridge-v2
git pull --ff-only
python3 tools/install_codex_uwa_commands.py
```

Enter the UWA route:

```bash
codex-uwa
```

Return to the normal signed-in official Codex provider:

```bash
codex-official
```

Direct provider switching is also available:

```bash
python3 tools/codex_provider_switch.py uwa
python3 tools/codex_provider_switch.py official
```

Useful local checks:

```bash
curl -sS http://127.0.0.1:8199/health
python3 tools/codex_route_audit.py status
curl -sS http://127.0.0.1:8199/v1/codex/web-affinity
```

## Routing model

The controlled UWA defaults are:

```text
provider = uwa
model = chatgpt
reasoning effort = high
```

Long-running acceptance does not trust a UI label alone. The authoritative route is proven from the actual Responses request, Codex session metadata and metadata-only UWA wire evidence.

The bridge does not silently spend official Codex quota and does not silently downgrade reasoning quality. Unsupported route/effort combinations fail closed.

## Architecture

```text
Codex Desktop / CLI
        |
        v
OpenAI Responses request
        |
        v
UWA Codex Responses bridge
        |
        v
logged-in ChatGPT Web session
        |
        v
Responses function_call
        |
        v
Codex executes the local client tool
        |
        v
function_call_output
        |
        v
conversation / Responses continuation
        |
        v
response.completed
```

## Tool contract

When the user explicitly requires a real local client tool such as `exec_command`, a textual simulation is not accepted. The bridge must deliver a real Responses `function_call`, allow Codex to execute it locally, accept the matching `function_call_output`, and continue the turn.

A bounded repair path exists for Web responses that initially omit an explicitly required client tool. It is designed to recover the function call without duplicating an already-completed local side effect.

## Continuity and Web session affinity

V2 uses `previous_response_id`, call-id continuity and ChatGPT conversation affinity to keep tool rounds and follow-up turns attached to the right logical conversation where possible.

If an affinity mapping is lost after a restart or expires, the bridge can reconstruct continuity from process-local and private persisted state. Correctness takes priority over forcing reuse of an unhealthy browser conversation.

## Metadata-helper isolation

Modern Codex clients can emit hidden structured helper requests such as thread-title generation. These may embed the user's actual task text as data.

V2 classifies those requests separately from agent turns. Recognized metadata helpers are answered locally and deterministically and do not enter the ChatGPT coding lane, required-tool detection, normal conversation affinity, or authoritative agent-route accounting.

```text
request_kind = metadata_helper   -> local deterministic helper path
request_kind = agent_turn        -> normal Codex / UWA reasoning path
```

## Hybrid routing safety

Hybrid H0-H5 are closed:

```text
H0 metadata-only route audit                  PASS
H1 exact provider/model/effort guard          PASS
H2 fresh Desktop route probe                  PASS / LIVE
H3 official -> UWA stateful handoff           PASS / LIVE
H4 private metadata-only transition ledger    PASS
H5 aggregate hybrid acceptance                PASS
```

The first release uses an explicit handoff model. Durable local project state and Git state are authoritative across provider transitions. Private transition metadata stores route information and hashed identities only, not prompt or tool bodies.

## Streaming cancellation hardening

M4 used this repository itself as the real-project pilot. The selected production hardening target was the V2 streamed Responses backing task.

When an outer streamed response is cancelled or explicitly closed, the backing `_run_chat_completion_final` task must not remain alive as orphan browser/request work. The final contract requires:

```text
consumer cancellation propagates to the caller
backing task is cancelled and awaited
explicit async-generator close cleans backing work
workflow reuse hint ends false
normal completion does not cancel an already-finished worker
request-manager returns to zero
```

The original real-project M4 turn sustained real tool/result continuation for roughly twelve minutes without a stream-disconnect failure. Recovery then isolated and validated the cancellation behavior with deterministic stdlib tests.

## Observability

Metadata-only Codex wire traces live under:

```text
~/.uwa/debug/codex-wire
```

They are used to prove protocol facts such as route, response status and real function-call names without storing prompt text, source code, command bodies or tool output by default.

Full capture may contain private data and must never be committed to a public repository.

## Release path

```text
M1 same-thread post-remote recovery             PASS / CLOSED
M2 minimal continuity blockers                  PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                 PASS / LIVE / CLOSED
M3b Desktop D1-D5                               PASS / LIVE / CLOSED
M4 real-project long-task pilot                 PASS / LIVE / CLOSED
M5 final A-F + compaction + restart regression  CURRENT
M6 CI + public-repo safety + docs/provenance
M7 topology inspection + merge to main
```

After the verified V2 branch reaches `main`, the next phase is a dependency audit and extraction of the bridge core plus genuinely required upstream runtime into a clearer standalone attributed repository.

## Security defaults

The intended local defaults are conservative:

```text
API bind           127.0.0.1
CORS               disabled
Debug              disabled
Unsafe Python      disabled
Auto update        disabled
Remote access      disabled
DevTools           local only
```

Never commit credentials, cookies, browser profiles, private UWA/Codex logs, private prompts, command/tool bodies, raw session or browser identifiers, private Responses persistence, or full wire traces.

## Attribution and license

This repository is derived from `lumingya/universal-web-api` and reuses its browser/API/runtime foundation. Those portions remain subject to the upstream AGPL-3.0 and applicable copyright/license obligations.

The V2 work also studies public Codex/Responses bridge implementations for compatibility and reliability ideas. Directly reused code, if any, must carry explicit file-level attribution and compatible licensing documentation.

See `docs/REFERENCES_AND_ATTRIBUTION.md` for detailed provenance information.

## Unofficial project notice

This is an independent learning, interoperability and engineering-validation project. It is not an official OpenAI, ChatGPT or Codex product and does not imply partnership, authorization or endorsement.

The project does not alter third-party account entitlements, subscription limits, quotas or model availability. Users remain responsible for complying with the software, website and service terms, policies and laws that apply to their use.
