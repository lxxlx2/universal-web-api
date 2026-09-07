# Stage F restart continuity — 2026-09-07

## Goal

Verify that an existing Codex thread can continue after UWA process restart, when process-local ChatGPT web-session and call-id affinity have been lost.

The recovery path may use Codex thread history, private persisted UWA Responses state, and the documented fresh-chat plus reconstructed-history fallback. Local execution must still occur through the Codex client.

## Pre-restart checkpoint

Stage F turn 1 has completed successfully on the synthetic acceptance workspace.

Observed evidence:

```text
prepare context fixture: PASS
preflight context fixture: PASS
fresh Codex thread created: PASS
turn 1 assistant reply: CONTEXT_READY
context/result.txt after turn 1: ABSENT
```

The Stage F context token therefore remains conversation-only before restart. The public repository intentionally does not record the live Codex thread identifier.

The turn was executed through `codex exec`. That client process exited after turn 1, so the next `codex exec resume` invocation also exercises Codex CLI process restart. The remaining disruptive boundary is UWA restart, which must clear process-local web affinity before the same Codex thread is resumed.

## Next gate

1. stop UWA;
2. start UWA again and verify health;
3. recover the existing Stage F thread identifier locally from the private turn-1 JSONL;
4. send `context_2` through `codex exec resume` without repeating the token;
5. require the same thread id on resume;
6. require a real local tool call to create and read `context/result.txt`;
7. require `CONTEXT_PASS` and the independent context checker to return `ACCEPTANCE_PASS`.

Do not prepare/reset the context fixture between turn 1 and turn 2, because doing so would invalidate the restart-continuity scenario.

## Status

```text
Stage F turn 1 pre-restart baseline   PASS
UWA restart                            NEXT
same-thread post-restart resume        pending
independent context checker            pending
Stage F overall                        IN PROGRESS
```

## Recording rule

This checkpoint is committed before restarting UWA so another collaborator can recover the exact project state even if the current chat or local runtime context is lost.
