# P1.2 required-tool continuation fix — CI PASS — 2026-09-08

Status: implementation and CI PASS; bounded live recovery rerun is CURRENT.

Live diagnosis established that the recovery turn executed the exact same workspace-guard `exec_command` twice. Both calls completed successfully with identical command/output fingerprints, while the recovery result file was never written. This identified duplicate required-tool enforcement across Codex Responses continuations.

The first implementation attempt added a second continuation patch layer. Security hardening run #444 correctly failed two newly added safety-boundary tests and exposed that `codex_v2_runtime_hardening.py` already contained an older duplicate-suppression wrapper.

The repair was consolidated into the existing runtime-hardening implementation instead of stacking another monkey patch:

- completed required-tool evidence is scoped to items after the latest user message;
- a tool is completed only with a matching call id across a real function/tool call and its output/result;
- older user-turn calls cannot satisfy a newer user turn;
- unmatched calls or outputs do not satisfy the requirement;
- a completed different tool does not satisfy the required tool;
- explicit request-level `tool_choice` remains authoritative;
- the temporary redundant continuation patch layer was removed.

Security hardening run #450 for head `aff5656e4fbc19a6b27f0ca2971b04a9b854346b` completed successfully across all jobs, including public repository safety, macOS and Ubuntu Python 3.11/3.13 checks, and the full reproducible upstream regression suite.

Next live action is intentionally bounded: restart UWA to load the consolidated runtime fix, confirm health/provider state, and rerun only the already-established same-thread post-remote recovery with a 300-second timeout. Do not rerun the long filler/compaction trigger.

No private thread id, prompt body, tool body, conversation-only token, browser identifier, account detail, or local process identifier is recorded here.
