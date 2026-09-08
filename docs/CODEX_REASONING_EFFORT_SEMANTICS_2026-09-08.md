# UWA reasoning-effort semantics — 2026-09-08

## Decision

The Codex Desktop/CLI reasoning control is not treated as authoritative merely because a slider or menu is visible. The authoritative contract is the reasoning effort that reaches UWA in the Responses request and the reasoning mode that UWA can verify on the controlled ChatGPT Web tab.

Current UWA semantics:

```text
UWA default                       high
Codex request effort=medium       supported
Codex request effort=high         supported
Codex request effort=low/light    unsupported / fail closed
```

The versioned UWA provider switch currently writes `model_reasoning_effort = "high"`, so a fresh UWA-mode Codex process defaults to High unless a genuine client/thread-level request override reaches the bridge.

## Runtime behavior

`app/services/codex_web_policy.py` normalizes the incoming Responses reasoning value and accepts only `medium` and `high` (plus aliases that normalize to `high`). Unsupported values raise `ChatGPTWebModeError` rather than silently collapsing to High.

`app/services/chatgpt_web_mode.py` applies the resolved effort to the controlled ChatGPT page:

```text
medium -> select Medium / 中
high   -> select High / 高
```

The bridge then inspects the page again and requires the selected reasoning state to match in strict mode.

Therefore Medium and High are intentionally distinct UWA modes and must not be documented as equivalent.

## Desktop UI interpretation

A visible Codex Desktop slider/menu is only a candidate client-side selection. Its visual position alone does not prove that UWA used that effort.

A reasoning-effort change counts as effective only when:

1. the request reaching UWA carries the intended effort, or the documented UWA default applies;
2. UWA normalizes that effort successfully;
3. ChatGPT Web is switched to the corresponding Medium/High mode;
4. bridge verification confirms the page state.

This matters when an already-running Desktop process was started before a provider/config switch, because its UI can display process-local or thread-local state that differs from a newly launched CLI process.

## Current usage guidance

```text
High    recommended/default and already used by the managed UWA provider contract
Medium  supported when the actual Responses request carries medium
Low     unsupported by the current UWA bridge
```

Do not claim that moving the Desktop slider changes UWA reasoning unless request + web-mode evidence confirms it.

## Future Desktop acceptance

Add after the current P1.2 remote-compaction work:

```text
R1 fresh UWA Desktop thread defaults to High
R2 select Medium -> request reports medium -> ChatGPT page verifies Medium
R3 select High   -> request reports high   -> ChatGPT page verifies High
R4 Low/Light is hidden, rejected, or explicitly reported unsupported under UWA
R5 official provider restore returns normal account-driven reasoning/model controls
```
