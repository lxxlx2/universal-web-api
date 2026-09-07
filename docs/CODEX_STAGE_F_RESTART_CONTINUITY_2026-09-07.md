# Stage F restart continuity — 2026-09-07

## Goal

Verify that an existing Codex thread can continue after UWA process restart, when process-local ChatGPT web-session and call-id affinity have been lost.

The recovery path may use Codex thread history, private persisted UWA Responses state, and the documented fresh-chat plus reconstructed-history fallback. Local execution must still occur through the Codex client.

## Pre-restart checkpoint

Stage F turn 1 completed successfully on the synthetic acceptance workspace.

Observed evidence:

```text
prepare context fixture: PASS
preflight context fixture: PASS
fresh Codex thread created: PASS
turn 1 assistant reply: CONTEXT_READY
context/result.txt after turn 1: ABSENT
```

The Stage F context token therefore remained conversation-only before restart. The public repository intentionally does not record the live Codex thread identifier.

The turn was executed through `codex exec`. That client process exited after turn 1, so the later `codex exec resume` invocation also exercises Codex CLI process restart.

## UWA restart checkpoint

The disruptive UWA restart boundary has now been verified.

Observed evidence:

```text
UWA listener before restart: present
UWA stop: PASS
listener after stop: absent
UWA listener after restart: present with a different process id
UWA_PROCESS_RESTART: PASS
health after restart: healthy
web affinity before restart: binding_count=4
web affinity after restart: binding_count=0
web affinity persistent: false
fallback: fresh_chat_plus_reconstructed_history
private turn-1 JSONL record: present
context/result.txt after restart: ABSENT
```

This proves that Stage F has crossed a real UWA process restart and that the process-local web affinity map did not survive. The browser itself may remain connected, but the new UWA process reports zero affinity bindings and zero tracked requests.

No live process id, thread id, browser conversation id, local log content, SQLite content, or other private runtime identifier is committed.

## Next gate

1. recover the existing Stage F thread identifier locally from the private turn-1 JSONL;
2. generate `context_2` from the acceptance harness;
3. send `context_2` through `codex exec resume` without repeating the token;
4. require the resumed event to report the same Codex thread id;
5. require real local tool execution to create and read `context/result.txt`;
6. require assistant reply `CONTEXT_PASS`;
7. run the independent context checker and require `ACCEPTANCE_PASS`.

Do not prepare or reset the context fixture between turn 1 and turn 2.

## Status

```text
Stage F turn 1 pre-restart baseline   PASS
UWA restart                            PASS
process-local web affinity cleared     PASS
same-thread post-restart resume        NEXT
independent context checker            pending
Stage F overall                        IN PROGRESS
```

## Recording rule

This checkpoint is committed before the post-restart resume so another collaborator can recover the exact project state even if the current chat or local runtime context is lost.
