# Codex Desktop D4 live pass — 2026-09-09

## Result

Desktop D4 double-restart recovery is PASS on the real Codex Desktop UI path.

The test used the generated `context` acceptance fixture under `~/uwa-codex-acceptance` and the managed UWA route. The first turn established conversation-only context. Codex Desktop was then fully exited, the versioned UWA lifecycle path was exercised, Desktop was reopened, the same Desktop history thread was resumed, and the second turn recovered the hidden context and completed the local artifact check.

## Machine-auditable evidence

```text
context: PASS
ACCEPTANCE_PASS
configured provider = uwa
configured model = chatgpt
configured effort = high
latest session provider = uwa
latest session model = chatgpt
latest session effort = high
session identity before/after restart boundary = MATCH
post-marker UWA requests = 3
post-marker UWA responses = 3
latest UWA status = completed
ROUTE_EXPECTATION_PASS = YES
ROUTE_EXPECTATION_FAILURES = NONE
post-restart metadata response count = 3
post-restart exec_command present = YES
post-restart completed response present = YES
```

The real session identity value, thread identifier, process identifiers, browser identifiers, prompts, command bodies and private trace contents are intentionally omitted.

## UWA restart boundary

The installed `codex-uwa` / `codex-uwa-stop` commands are thin wrappers over repository-tracked lifecycle code. The stop path is fail-closed and does not report success until TCP 8199 is empty. The restart path stops the old owned listener, starts a healthy owned listener, and rejects any reused listener PID. Therefore a successful versioned lifecycle run provides the product-level listener replacement invariant required by D4; raw live PIDs are deliberately not committed.

Relevant implementation:

- `tools/install_codex_uwa_commands.py`
- `tools/codex_uwa_lifecycle.py`

## What D4 proves

D4 proves that the actual Desktop history path can recover the same UWA-backed Codex thread after both a Desktop process boundary and a UWA process boundary, while preserving conversation context and retaining real client-side tool execution on a fresh healthy UWA route.

## Gate transition

```text
Desktop D1 local tool round trip              PASS / CLOSED
Desktop D2 same-thread continuation           PASS / CLOSED
Desktop D3 Desktop restart + history resume   PASS / CLOSED
Desktop D4 Desktop + UWA restart recovery     PASS / CLOSED
Desktop D5 official-account restore           READY / CURRENT
```

D5 is now the active Desktop gate. It must restore normal signed-in official-account mode without a pinned UWA provider/model/reasoning setting and verify a harmless official Codex task when official quota is available.
