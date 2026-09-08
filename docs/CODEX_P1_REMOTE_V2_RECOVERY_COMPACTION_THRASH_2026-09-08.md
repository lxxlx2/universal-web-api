# P1.2 post-remote recovery compaction thrash — 2026-09-08

## Live observation

A read-only rollout check after the bounded post-remote recovery timeout reported:

- private recovery thread recovered: yes
- rollout located: yes
- compaction markers before the last recovery attempt: 5
- compaction markers after the zero-progress recovery attempt: 6
- compaction grew during a turn that produced zero agent messages, zero completed client commands, zero file changes and zero MCP calls

## Interpretation

This isolates the current blocker to post-compaction re-entry / compaction thrash. The recovery prompt did not reach an ordinary model/tool phase before another compaction lifecycle marker was appended.

This is not evidence of a required-tool parser failure, workspace failure, ChatGPT Web 403, or a recovered-token mismatch.

## Current gate

P1.2 remains open. The next code/CI task is to determine why the compacted continuation is still considered above the auto-compaction threshold and prevent immediate repeated compaction without weakening normal threshold protection.

No private thread id, rollout path, account identifier, prompt body or synthetic token is recorded here.
