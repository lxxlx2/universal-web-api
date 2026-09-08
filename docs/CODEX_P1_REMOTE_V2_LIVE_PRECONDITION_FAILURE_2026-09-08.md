# P1.2 native remote V2 live — invalid precondition checkpoint — 2026-09-08

## Classification

The first attempt is **INVALID PRECONDITION**, not a remote-compaction protocol failure.

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

No conclusion about the remote V2 protocol implementation should be drawn from that run.

## Incidental shell issue

The pasted zsh command contained standalone `#` comment lines. The user's interactive shell did not have `interactivecomments` enabled, producing:

```text
zsh: command not found: #
```

This did not cause the provider precondition failure. Future operator commands avoid standalone comment lines.

## Subsequent transient network blocker

Before the corrective UWA-mode precondition run, a separate operator attempt stopped at:

```text
fatal: unable to access 'https://github.com/lxxlx2/universal-web-api.git/':
Could not resolve host: github.com
```

The command used `set -e`, so it exited at `git pull --ff-only` before executing the provider switch, memory guard, UWA config verification, health check, capability shim, or any Codex acceptance turn.

This is classified **OPERATOR NETWORK / DNS TRANSIENT**, not a UWA/Codex product failure and not a remote-compaction protocol attempt.

## Resolution

The intended corrective precondition run was then rerun successfully. Current evidence is recorded separately in:

- `docs/CODEX_P1_REMOTE_V2_PRECONDITION_LIVE_PASS_2026-09-08.md`

Key resolution markers:

```text
MODEL_PROVIDER_UWA=YES
MODEL_CHATGPT=YES
REASONING_HIGH=YES
APPROVAL_ON_REQUEST=YES
SANDBOX_WORKSPACE_WRITE=YES
PROVIDER_NAME_BASELINE=YES
LOOPBACK_BASE_URL=YES
WIRE_API_RESPONSES=YES
OPENAI_AUTH_DISABLED=YES
WEBSOCKETS_DISABLED=YES
UWA_PROVIDER_CONTRACT_PASS=YES
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
UWA_REMOTE_V2_PRECONDITION_PASS
```

## Gate status

```text
P1.2 remote V2 implementation/CI             PASS
P1.2 native remote compact attempt #1        INVALID PRECONDITION
P1.2 transient GitHub DNS blocker            CLOSED / non-product
P1.2 UWA provider precondition live          PASS
P1.2 native remote compact macOS live        CURRENT
```
