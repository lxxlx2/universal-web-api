# S1 standalone dependency/import/runtime audit gate — 2026-09-10

## State

`S1 CURRENT`

The verified Codex Web Bridge V2 integration is already on `main`. S1 runs on a separate post-main branch, `codex-standalone-s1`, so dependency discovery cannot mutate the released baseline.

Source baseline:

```text
main verified release head        a140002e65a02a3323abcde3e1fdb8674710c996
post-main audit branch            codex-standalone-s1
released product scope            frozen during S1
```

## Goal

Produce evidence for the smallest standalone repository that can preserve the verified bridge behavior. File inclusion and exclusion must come from import/runtime evidence rather than filename guessing.

The audit classifies reachable files into:

```text
core
required_upstream_runtime
validation
validation_or_operator
required_support
```

The final S1 manifest will also separate external import roots from the current `requirements.txt` distribution list. Import-root-to-package mapping is reviewed explicitly because the two names are not always identical.

## Audit entry points

The first-pass static graph starts from the released Codex bridge surface:

```text
app/api/codex_responses_v2.py
app/api/codex_compact.py
app/api/codex_compat.py
app/services/chatgpt_web_*.py
app/services/client_tool_policy.py
app/services/codex_*.py
app/services/tool_calling.py
app/core/workflow/executor_send.py
tools/codex_provider_switch.py
tools/codex_uwa_lifecycle.py
tools/install_codex_uwa_commands.py
tools/public_repo_safety_check.py
```

The graph recursively resolves local Python imports and records every reachable repository Python file.

## Runtime smoke

Static analysis alone is insufficient because imports can be conditional or dynamic. The S1 tool therefore also launches a child Python process and import-smokes the release-critical runtime modules without sending Web requests or invoking browser work:

```text
app.api.codex_responses_v2
app.api.codex_compact
app.services.codex_remote_compaction_v2
app.services.codex_wire_observability
app.services.codex_web_session_affinity
app.services.client_tool_policy
```

It records loaded repository files and external import roots. Raw local paths are kept only in private local audit state.

## Privacy and repository safety

`tools/codex_s1_dependency_audit.py` is repository-read-only. It requires a clean `codex-standalone-s1` worktree and writes the detailed manifest only below private `~/.uwa/s1-audit` state.

It does not print or commit browser/session identifiers, prompts, tool bodies, local absolute paths, cookies, credentials or runtime traces.

## Pass contract

The first S1 audit run passes when:

```text
S1_PROJECT_BRANCH=codex-standalone-s1
S1_REPOSITORY_CLEAN=YES
S1_SEEDS_PRESENT=YES
S1_PARSE_ERROR_COUNT=0
S1_STATIC_REACHABLE_FILE_COUNT>0
S1_RUNTIME_SMOKE=PASS
S1_RUNTIME_IMPORT_ERROR_COUNT=0
S1_PRIVATE_MANIFEST_WRITTEN=YES
S1_DEPENDENCY_AUDIT=PASS
```

A PASS here means the dependency evidence was collected successfully. It does not close S1 by itself.

## S1 closure work after the first run

After receiving the private-audit summary counts, S1 will:

1. inspect the generated static/runtime closure;
2. identify required upstream browser/workflow/config/logging modules;
3. map external import roots to installable distributions;
4. classify broad UWA surfaces that have no bridge dependency evidence as exclusion candidates;
5. produce a committed public core manifest containing paths/categories only, with no private runtime data;
6. cross-check license/copyright/provenance obligations for every retained upstream-derived area;
7. define the exact S2 extraction set and validation matrix.

Only then does S1 become `PASS / CLOSED` and S2 begin.

## Remaining post-main path

```text
S1 dependency/import/runtime audit + core manifest   CURRENT
S2 standalone attributed repository                  pending
S3 full CI + CLI/Desktop/live parity acceptance      pending
S4 first standalone research release                 pending
```
