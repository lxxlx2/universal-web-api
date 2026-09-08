# P1.2 post-remote recovery timeout — 2026-09-08

Status: LIVE FAILURE / DIAGNOSTIC CURRENT

The same-thread post-remote recovery gate was rerun after the ChatGPT Web 403 precheck recovered.

Observed public-safe evidence:

- private trace contract valid
- original thread recovered
- prior remote-V2 trigger contract still PASS
- rollout compact marker count before this recovery attempt increased to 3
- workspace token leak before recovery remained NO
- recovery turn timed out after the configured 900 seconds

This does not invalidate the already-proven remote-V2 compaction live PASS. It also does not yet establish a memory-continuity failure.

The increase from one to three compact markers means repeated recovery attempts are mutating the long-running thread by triggering additional compactions. Do not keep blindly replaying the same recovery turn. The next step is a read-only, redacted inspection of the latest `post-remote-recovery.jsonl` to determine whether the turn executed local commands, encountered a web/transport failure, entered another compaction cycle, or stalled after a tool-output continuation.

No private prompt body, thread identifier, token, local trace contents, listener PID, browser identifier, or account detail is recorded here.
