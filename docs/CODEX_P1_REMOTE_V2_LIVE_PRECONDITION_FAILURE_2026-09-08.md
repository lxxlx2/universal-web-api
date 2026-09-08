# P1.2 native remote V2 live — invalid precondition checkpoint — 2026-09-08

## Classification

This attempt is **INVALID PRECONDITION**, not a remote-compaction protocol failure.

Observed live output:

```text
REMOTE_COMPACTION_COMPAT=INVALID
ERROR=top-level model_provider is not uwa

REMOTE_COMPACTION_COMPAT=FAIL
ERROR=top-level model_provider is not uwa

MODEL_PROVIDER_UWA=NO
PROVIDER_NAME_AZURE=NO
REMOTE_CAPABILITY_CONTRACT_PASS=NO

SEED_REPLY_EXACT=NO
RUN_FAIL seed_contract
```

## Meaning

The fail-closed capability helper behaved correctly: it refused to modify the Codex provider because the top-level `model_provider` was not `uwa`.

The probe therefore did not execute under the intended UWA provider contract. Its final `seed_contract` failure cannot be used to evaluate native remote compaction V2.

No conclusion about the remote V2 protocol implementation should be drawn from this run.

## Incidental shell issue

The pasted zsh command contained standalone `#` comment lines. The user's interactive shell did not have `interactivecomments` enabled, producing:

```text
zsh: command not found: #
```

This did not cause the provider precondition failure, but future operator commands should avoid standalone comment lines or explicitly enable interactive comments.

## Operator network transient before precondition retry

The first retry command stopped at `git pull --ff-only` before any UWA/provider mutation because the local Mac could not resolve GitHub DNS:

```text
fatal: unable to access 'https://github.com/lxxlx2/universal-web-api.git/': Could not resolve host: github.com
```

Classification: **operator-network transient / no product signal**.

At failure time Git had already reported that the local branch was on `codex-web-bridge-v2` and up to date with its currently known `origin/codex-web-bridge-v2`. Because the shell was running with `set -e`, no later provider-switch, memory-guard, contract verification, or remote-compaction probe step executed.

The next action is therefore only to confirm DNS/HTTPS access to GitHub and complete a fast-forward pull. Do not run the UWA/provider precondition sequence until network reachability is restored.

## Valid next gate

Before rerunning the native remote-compaction probe:

1. confirm local GitHub DNS/HTTPS reachability and complete `git pull --ff-only`;
2. explicitly switch the versioned Codex config into UWA mode;
3. verify `model_provider = "uwa"` and the managed UWA root/provider contract;
4. enable the fail-closed remote-compaction capability shim;
5. verify only the provider display name changed to `Azure`;
6. use a fresh Codex CLI process for the remote V2 probe.

The UWA listener itself was healthy during the invalid attempt:

```text
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
```

## Gate status

```text
P1.2 remote V2 implementation/CI             PASS
P1.2 native remote compact macOS attempt #1  INVALID PRECONDITION
precondition retry #1                        BLOCKED: operator GitHub DNS
P1.2 native remote compact macOS live        CURRENT
```
