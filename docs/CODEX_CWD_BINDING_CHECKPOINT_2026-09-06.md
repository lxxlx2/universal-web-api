# Codex cwd binding checkpoint - 2026-09-06

## Live finding

A fresh Codex Desktop thread was created under the visible `uwa-codex-acceptance` project and asked to execute a minimal workspace probe through `exec_command`.

Observed client output:

```text
/
MARKER=NO
SCENARIO=NO
```

This means the local command executed with `/` as its effective working directory even though the Desktop UI showed the acceptance project selected. The Stage B run that returned `ACCEPTANCE_WORKSPACE_MISMATCH` is therefore classified as an execution-context/cwd-binding failure, not a web-model reasoning failure and not a successful Stage B acceptance.

## What upstream Codex does

Current upstream `exec_command` resolves its effective cwd from the turn environment when the tool call does not provide a `workdir`. If a relative `workdir` is provided, it is resolved against the turn environment cwd. Therefore `/` can come from either:

1. the Codex turn environment itself being rooted at `/`; or
2. the model/tool adapter explicitly supplying an absolute root workdir.

The current UWA tool prompt does not intentionally force `/`; it asks the model to use the declared client tool and treats the Codex client as authoritative for local execution.

## Next diagnostic

Use the refreshed official Codex provider on the same visible Desktop project and run the same probe in a brand-new official thread:

```text
pwd && printf 'MARKER=' && test -f .uwa_codex_acceptance && echo YES || echo NO && printf 'SCENARIO=' && test -d failure_recovery && echo YES || echo NO
```

Interpretation:

- Official provider returns the acceptance directory + YES/YES: Desktop project binding is healthy; the custom-provider/UWA path is altering or losing cwd/tool arguments.
- Official provider also returns `/` + NO/NO: the issue is in Codex Desktop project/thread binding and is independent of UWA.

The next UWA instrumentation should record only safe tool metadata for `exec_command` (whether `workdir` was present and whether it was `/`), without logging command contents or private file data.

## Concurrent web requests

The same live session also showed additional UWA requests timing out while one ChatGPT tab was busy. A previously started Codex memory-consolidation flow (`gpt-5.6-terra`) was observed in the same period. UWA mode now includes a memory guard that disables new Codex memory generation/use and restores prior values when returning to the official provider. Already queued/claimed background work may still exist until Codex is fully quit.

## Safety / persistence

Switching back to the official provider does not remove:

- the `security-hardening` Git branch or commits;
- acceptance fixtures under the local synthetic workspace;
- tracked README/current-state/acceptance documents;
- the private UWA continuation database;
- existing Codex thread history.

The UWA process can remain stopped while official Codex is used. Resume bridge testing later by switching back to UWA and reading the canonical handoff files before continuing.
