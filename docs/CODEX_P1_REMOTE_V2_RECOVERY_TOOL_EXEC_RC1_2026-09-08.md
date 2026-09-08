# P1.2 Post-Remote Recovery — Tool Execution Reached, Turn Still Failed

Date: 2026-09-08
Branch: `codex-web-bridge-v2`

## Classification

Live recovery rerun remains **FAIL / CURRENT**.

This rerun materially differs from the prior failure: the required-tool language parser fix is active and the recovery turn reached a real client command execution lifecycle before the Codex turn exited with `rc=1`.

## Verified preconditions

- UWA listener restarted onto the latest branch code.
- UWA health passed with browser connected.
- provider remained `model_provider="uwa"`.
- remote-compaction capability shim remained enabled under the bounded Azure-name compatibility contract.
- focused runtime check returned `REQUIRED_TOOL='exec_command'` and `REQUIRED_TOOL_PATCH_PASS=YES`.
- original private remote-compaction trace was recovered successfully.
- prior remote-compaction contract remained valid.
- no synthetic recovery token was present in the acceptance workspace before the recovery turn.

## Live rerun result

The recovery runner stopped at the Codex turn boundary with:

```text
RUN_FAIL recovery_turn=Codex turn failed rc=1
```

A subsequent private-trace shape inspection reported:

```text
EVENT_COUNTS=error:1,item.completed:2,item.started:1,thread.started:1,turn.failed:1,turn.started:1
ITEM_COUNTS=command_execution:2,error:1
NONJSON_LINE_COUNT=0
```

This is sufficient to establish that the previous zero-tool-call failure has changed: at least one real command execution lifecycle was emitted before the turn failed.

## Important screenshot evidence

The controlled ChatGPT Web conversation visibly contained compacted prior context that included an earlier assistant statement claiming no `exec_command` tool was available and therefore that the first required workspace step could not be completed. That stale incorrect claim may have been preserved inside the compacted context. It is a relevant clue but is **not yet classified as the root cause** because the repaired rerun did in fact reach a real command execution lifecycle.

## Current boundary

Do not rerun the full large-context or remote-compaction trigger probe.

Next diagnostic is limited to the private recovery trace and must determine:

1. whether the first command execution completed successfully,
2. whether it was the intended workspace guard step,
3. the structured shape/category of the `error` and `turn.failed` events,
4. whether failure occurred while returning the first tool result to the Responses bridge, during the required-tool continuation, or in transport/session recovery.

Private prompt bodies, thread identifiers, command output bodies, account details, and synthetic token values must remain uncommitted.
