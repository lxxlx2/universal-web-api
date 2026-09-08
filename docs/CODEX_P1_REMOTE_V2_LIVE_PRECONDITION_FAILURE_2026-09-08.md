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

## Valid next gate

Before rerunning the native remote-compaction probe:

1. explicitly switch the versioned Codex config into UWA mode;
2. verify `model_provider = "uwa"` and the managed UWA root/provider contract;
3. enable the fail-closed remote-compaction capability shim;
4. verify only the provider display name changed to `Azure`;
5. use a fresh Codex CLI process for the remote V2 probe.

The UWA listener itself was healthy during this invalid attempt:

```text
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
```

## Gate status

```text
P1.2 remote V2 implementation/CI             PASS
P1.2 native remote compact macOS attempt #1  INVALID PRECONDITION
P1.2 native remote compact macOS live        CURRENT
```
