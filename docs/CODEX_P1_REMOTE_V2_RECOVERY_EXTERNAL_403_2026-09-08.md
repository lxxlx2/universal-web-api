# P1.2 post-remote recovery external 403 blocker — 2026-09-08

Status: EXTERNAL BLOCKER / INCONCLUSIVE for the recovery gate. This is not recorded as a protocol regression and not recorded as PASS.

Observed live evidence after the required-tool language fix:

- The recovery resumed the same previously compacted Codex thread.
- The prior remote-V2 compact lifecycle was already proven before this rerun.
- The recovery request now produced a real local `command_execution`.
- The first workspace guard command completed successfully with exit code 0.
- The command was the intended acceptance workspace guard and did not search private Codex/UWA history or token stores.
- After the first successful tool execution, the turn failed because ChatGPT Web returned HTTP 403 with an `Unusual activity has been detected from your device. Try again later.` message.
- The structured failure is transport/HTTP 4xx, not required-tool, tool-choice, previous-response, context-limit, or local workspace failure.

Interpretation:

1. The earlier parser defect is fixed: required-tool enforcement now reaches a real client tool call.
2. The earlier `ACCEPTANCE_WORKSPACE_MISMATCH` result is disproven by the successful real workspace guard.
3. This rerun cannot determine whether the second and third recovery steps would succeed because the backing ChatGPT Web request was blocked by an external 403 before completion.
4. Do not hammer retries while this risk-control response is active. Resume only after the external condition clears.

Next gate after cooldown/recovery of normal ChatGPT Web access:

- rerun only the same-thread post-remote recovery runner;
- do not rebuild the long-context thread or retrigger compaction;
- require the remaining write/read tool lifecycle and exact conversation-only token recovery before closing P1.2.
