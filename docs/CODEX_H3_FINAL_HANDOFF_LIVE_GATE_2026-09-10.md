# Codex H3 final handoff live gate — 2026-09-10

## Purpose

Close H3 with one synthetic official-to-UWA stateful handoff using the already-preserved official source state. The official source half must not be rerun.

The one-shot helper is:

```text
tools/codex_h3_final_handoff_live.py
```

## Preconditions

```text
project branch = codex-web-bridge-v2
project worktree = clean
configured route = uwa / chatgpt / high
UWA browser = connected
UWA running requests = 0
synthetic effects.log = BASELINE + OFFICIAL_EFFECT_ONCE
independent official source checker = PASS
```

## Action

The helper starts one fresh `codex exec` agent turn in the preserved synthetic workspace. The prompt requires the real local `exec_command` client tool, requires the agent to inspect durable state first, forbids replaying or rewriting the official source effect, appends `UWA_CONTINUATION_ONCE` only when absent, and runs the independent handoff checker.

The helper does not print the prompt, command body, tool output, raw thread identifier, browser identifier, PID, cookie or credential.

## PASS requirements

```text
official source effect count = 1
UWA continuation effect count = 1
independent handoff checker = PASS
real exec_command function call in agent trace = YES
at least one completed agent response = YES
metadata-helper traffic excluded from agent accounting = YES
agent request model/effort = chatgpt / high
authoritative route audit = uwa / chatgpt / high
request-manager running count after = 0
```

A hidden metadata helper cannot satisfy the real-agent requirements.

## After PASS

Record H3 as PASS / LIVE / CLOSED, advance Hybrid Routing Safety to H4/H5, update canonical state/progress/README and the Draft PR, then continue the accelerated merge gate.
