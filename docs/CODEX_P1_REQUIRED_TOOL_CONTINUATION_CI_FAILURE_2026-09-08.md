# P1.2 required-tool continuation fix — CI safety failure — 2026-09-08

Status: CI FAILURE, implementation not eligible for live rerun yet.

Security hardening run #444 completed with five jobs passing and `upstream-regression` failing. The reproducible suite result was:

- 506 passed
- 2 failed
- 2 deselected

The two failures were newly added safety-boundary tests:

1. a completed tool cycle from an older user turn must not satisfy a required tool in a newer user turn;
2. an explicit request-level `tool_choice` must remain authoritative even when a completed call/output cycle exists.

CI logs also exposed that `app/services/codex_v2_runtime_hardening.py` already contains a required-tool duplicate-suppression wrapper. The newly added continuation patch therefore overlapped an existing implementation. The older runtime wrapper scans the whole input history and can suppress too broadly, including the two unsafe cases above.

Next action:

- consolidate the continuation rule into the existing runtime-hardening implementation;
- scope completed call/output evidence to items after the latest user message;
- preserve explicit `tool_choice` as authoritative;
- remove the redundant additional patch layer;
- rerun the full reproducible regression before any live recovery rerun.

No private thread id, prompt body, tool body, token, browser identifier, or local process identifier is recorded here.
