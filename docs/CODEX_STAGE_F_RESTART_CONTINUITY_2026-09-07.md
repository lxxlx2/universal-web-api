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

The turn was executed through `codex exec`. That client process exited after turn 1, so the later `codex exec resume` invocation also exercised Codex CLI process restart.

## UWA restart checkpoint

The disruptive UWA restart boundary was verified.

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

This proves that Stage F crossed a real UWA process restart and that the process-local web affinity map did not survive.

## Post-restart same-thread resume checkpoint

The same Codex thread resumed successfully after the UWA restart.

Observed evidence:

```text
affinity before resume: binding_count=0
resumed thread id matched original thread id: PASS
THREAD_MATCH=YES
context_2 did not repeat the context token
real local command execution: PASS
local cwd: synthetic acceptance workspace
context/result.txt created: PASS
context/result.txt content: EMBER-7319\n
byte sequence: 45 4d 42 45 52 2d 37 33 31 39 0a
assistant reply: CONTEXT_PASS
affinity after resume: binding_count=2
```

The token was therefore recovered across a real UWA restart from the surviving continuity layers rather than from the destroyed pre-restart in-memory affinity map. The successful local command execution also confirms that restart recovery preserved real Codex client tool use.

No live process id, thread id, browser conversation id, local log content, SQLite content, or other private runtime identifier is committed.

## Independent checker

The final independent acceptance checker was run without resetting the fixture:

```bash
python3 tools/codex_desktop_acceptance.py check --scenario context
```

Observed result:

```text
context: PASS
ACCEPTANCE_PASS
```

## Final status

```text
Stage F turn 1 pre-restart baseline   PASS
UWA restart                            PASS
process-local web affinity cleared     PASS
same-thread post-restart resume        PASS
real local tool execution              PASS
CONTEXT_PASS                            PASS
independent context checker            PASS
Stage F overall                        PASS
```

Stage F is closed. This is the first completed live proof that the Codex + UWA workflow can survive a real UWA restart, lose process-local affinity, recover the same Codex thread without repeating the context token, resume real local tool execution, and still pass an independent checker.

## Next engineering phase

Proceed to production-hardening validation: long-context stress/recovery, deeper lost-affinity fallback coverage, and a real-project long-task pilot before final regression and merge to `main`.

## Recording rule

Every disruptive checkpoint and final acceptance result is committed before the next step so another collaborator can recover project state without relying on the current chat.
