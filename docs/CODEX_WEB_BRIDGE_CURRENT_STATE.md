# Codex Web Bridge current state

Last updated: 2026-09-07
Branch: `codex-web-bridge-v2`

This is the canonical handoff. Read this file, `README.md`, `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md`, `docs/CODEX_WEB_SESSION_AFFINITY_2026-09-07.md`, and Draft PR #2 before changing the bridge.

## Goal

Use Codex Desktop / CLI as the local coding client while routing reasoning through a controlled ChatGPT Web session. Filesystem, shell, tests, Git, sandbox and approval remain Codex-side capabilities.

```text
Codex Desktop / CLI
→ Responses-compatible request
→ UWA 127.0.0.1:8199
→ ChatGPT Web / GPT-5.6 Sol / High
→ web model chooses declared client tool
→ UWA emits Responses function_call
→ Codex executes locally
→ function_call_output returns
→ same ChatGPT conversation continues
```

## Live verified

- custom `uwa` provider loads in Codex Desktop and CLI;
- ordinary text inference through ChatGPT Web;
- GPT-5.6 Sol / High target web mode;
- minimal Codex Responses function-call SSE;
- real `exec_command` on macOS;
- correct Codex workspace cwd inheritance;
- real function-call-output continuation;
- single-file read/edit/test loop;
- Stage A multi-file acceptance: `ACCEPTANCE_PASS`;
- private Responses SQLite continuation implementation;
- Memories isolation in UWA mode;
- V2 metadata wire trace endpoint and local trace files.

Latest real cwd evidence:

```text
workdir: /Users/jerson/uwa-codex-acceptance
/bin/zsh -lc pwd in /Users/jerson/uwa-codex-acceptance
/Users/jerson/uwa-codex-acceptance
```

The old accidental `workdir="/"` issue is no longer the active blocker.

## Current blocker and V2 fix

The last short probe exposed a web-session lifecycle problem: one Codex task created multiple ChatGPT sidebar conversations and repeated the same successful `pwd` tool call.

Root cause:

1. the Codex web-mode preparation path forced a fresh composer before every outer Responses turn;
2. the generic ChatGPT UWA workflow also contains a `new_chat_btn` step and generic conversation reuse is disabled by default;
3. Responses history was reconstructed each outer turn, so a fresh ChatGPT conversation repeatedly saw the original explicit tool requirement.

V2 now introduces process-local web-session affinity:

```text
response_id A
→ validated ChatGPT /c/... pathname
→ next request previous_response_id=A
→ restore same /c/...
→ send only new Responses delta
→ response_id B remains on same conversation
```

The Codex browser round also applies a narrow request-scoped override so the generic UWA workflow skips its own `new_chat` step. This override is cleared after the Codex browser round and does not change ordinary UWA request behavior.

If affinity is missing or unhealthy, V2 falls back to fresh chat + reconstructed history.

Implementation and acceptance details: `docs/CODEX_WEB_SESSION_AFFINITY_2026-09-07.md`.

## V2 protocol observability

Default local trace:

```text
~/.uwa/debug/codex-wire
```

Metadata distinguishes real `function_call` items from assistant text that only resembles tool output. It records event/tool metadata and argument shape/hash, not prompt, source, command body, tool output, Cookie or Token.

Endpoints:

```text
GET /v1/codex/wire-trace
GET /v1/codex/web-affinity
```

Neither status endpoint exposes stored ChatGPT conversation paths.

## Required-tool contract

If a user explicitly requires a declared client tool, a plain-text imitation does not satisfy the turn. V2 requires a real Responses `function_call`, performs a bounded repair, then fails closed.

Required-tool repair now chains through the prior attempt response id so the repair remains in the same ChatGPT web conversation.

## Next live gate

Do not start Stage B yet.

Rerun the minimal `exec_command(pwd)` probe and require:

```text
real exec_command executes once
cwd is /Users/jerson/uwa-codex-acceptance
no repeated pwd loop
one ChatGPT conversation for the agent loop
web affinity binding is created
continuation reaches final answer
```

After that gate passes, run the marker/scenario probe and resume Stage B.

## Acceptance matrix

```text
single-file read/edit/test                 PASS
Stage A multi-file read/edit/test          PASS
real exec_command cwd                      PASS
V2 metadata wire trace                     PASS
V2 single-web-conversation tool loop       pending live recheck
Stage B failure recovery                   blocked on V2 gate
Stage C Git diff discipline                pending
Stage D long process + write_stdin         pending
Stage E same-thread continuity             pending
Stage F Codex + UWA restart continuity     pending
```

## Continuity model

Four layers:

1. Codex Desktop thread history.
2. UWA private Responses continuation store: `~/.uwa/codex_responses.sqlite3`.
3. process-local ChatGPT web-session affinity.
4. Git-tracked project checkpoints.

Web affinity is intentionally not persisted. A UWA restart loses that mapping and triggers the safe full-history fallback. Project state remains Git-first.

## Memories isolation

UWA acceptance keeps:

```toml
[memories]
generate_memories = false
use_memories = false
```

This does not delete Codex threads, Git state, project files, memory files or the Responses continuation DB.

## Security

- API and DevTools remain loopback-only by default;
- no public/LAN DevTools exposure;
- unsafe Python command-engine capability disabled;
- Codex sandbox and approval remain authoritative;
- web affinity stores only a validated ChatGPT pathname in process memory;
- private DB, browser profile, logs, cookies, `.env`, wire dumps and private workspace content are never committed;
- public docs/tests use synthetic or redacted examples only.

## Design references

See `docs/REFERENCES_AND_ATTRIBUTION.md`.

V2 studied browser tool-call round trips, Responses translation, sticky-session/TTL/queue designs and official Responses diagnostics from the referenced public projects. Current V2 additions are independently implemented; no reference-project source file was copied.

## Recovery after a new thread

```text
README.md
→ docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md
→ docs/CODEX_WEB_SESSION_AFFINITY_2026-09-07.md
→ docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md
→ git status
→ git log -8 --oneline
→ inspect relevant diff/tests
```
