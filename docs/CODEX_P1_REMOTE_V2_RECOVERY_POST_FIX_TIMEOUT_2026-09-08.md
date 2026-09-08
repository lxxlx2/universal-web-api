# P1.2 Remote V2 Recovery: post-fix bounded live timeout (2026-09-08)

## Status

`BOUNDED LIVE TIMEOUT — continuation state fix itself verified`

## Preconditions verified

- UWA health passed with browser connected.
- Top-level Codex provider remained `uwa`.
- Remote compaction compatibility remained enabled through the narrow provider-name capability shim.
- The consolidated required-tool continuation fix was present on the live branch and passed its local focused contract check:
  - natural-language required tool + matching call/output in the latest user turn => duplicate enforcement suppressed;
  - explicit request-level `tool_choice` => still authoritative.
- Prior native remote V2 trigger contract remained valid.
- Private thread recovery succeeded.
- Workspace token leak pre-check remained negative.

## Live result

The bounded same-thread recovery run did not reach a terminal result within 300 seconds and exited through the recovery runner timeout boundary.

Observed safe evidence:

- private trace directory validation: PASS
- private thread recovery: PASS
- prior remote-compaction trigger contract: PASS
- token leak before recovery: NO
- local continuation-state focused check: PASS
- live recovery turn: TIMEOUT at 300 seconds

No result-file acceptance evidence was produced, so P1.2 remains open.

## Interpretation

The previously observed duplicate workspace-guard enforcement is no longer sufficient to explain the remaining failure. The next debug step is to classify where the real continuation stops: before the first browser response, while waiting for a client tool call/output cycle, or after a tool result when the bridge should continue the same web conversation.

Do not increase the timeout or rerun the long recovery blindly. Inspect the versioned recovery runner and continuation-stream timeout/observability boundaries first, then add the smallest safe diagnostic needed to distinguish those states.

## Privacy

This checkpoint intentionally excludes live process identifiers, account details, private thread identifiers, local trace paths, conversation tokens, command bodies and private tool outputs.
