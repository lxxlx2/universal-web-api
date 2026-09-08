# Codex Desktop D3 live pass — 2026-09-09

## Result

Desktop D3 application-restart continuity is PASS on the real Codex Desktop UI path.

The test used the generated `context` acceptance fixture under `~/uwa-codex-acceptance` and the managed UWA route. The first turn established conversation-only context. Codex Desktop was then fully exited and reopened, the same Desktop history thread was resumed, and the second turn recovered the hidden context and completed the local artifact check.

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
session identity before/after Desktop restart = MATCH
post-marker UWA requests = 3
post-marker UWA responses = 3
latest UWA status = completed
ROUTE_EXPECTATION_PASS = YES
ROUTE_EXPECTATION_FAILURES = NONE
```

The real session identity value, thread identifier, process identifiers, browser identifiers, prompts, tool bodies and private trace contents are intentionally omitted.

## What D3 proves

D3 proves that the actual Codex Desktop history path can resume the same UWA-backed Codex thread after a full Desktop application exit/reopen and preserve the conversation context required by the acceptance fixture.

This is stronger than the earlier CLI `codex exec resume` evidence because the process boundary and history selection occurred through the Desktop product path.

## Gate transition

```text
Desktop D1 local tool round trip              PASS / CLOSED
Desktop D2 same-thread continuation           PASS / CLOSED
Desktop D3 Desktop restart + history resume   PASS / CLOSED
Desktop D4 Desktop + UWA restart recovery     READY / CURRENT
Desktop D5 official-account restore           pending
```

D4 is now the active Desktop gate. It must cross both the Desktop process boundary and a real UWA listener restart, then resume the same Desktop thread and pass the independent context checker on a fresh post-restart UWA route.
