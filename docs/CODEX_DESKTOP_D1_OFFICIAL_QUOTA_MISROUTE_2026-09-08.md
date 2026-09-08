# Desktop D1 official-quota misroute — 2026-09-08

## Classification

D1 is NOT PASS. During the first Desktop live attempt, the Desktop surface consumed the signed-in account's official Codex/Work five-hour allowance even though the managed local Codex config was set to the UWA provider before Desktop restart.

## User-visible evidence

- The Desktop UI showed an active pre-existing Codex conversation titled `Fix and harden V2 cargo flow`, not the fresh `uwa-codex-acceptance/multi_file` acceptance thread.
- The conversation performed edits and commands against a Unity project (`Assets/Game/...`, `Assets/Tests/...`).
- The Desktop UI then reported the Codex/Work usage limit was reached.
- The user confirmed the five-hour official allowance was effectively exhausted by this run.

No account identifiers, usage amounts, local PIDs, thread IDs, or private project contents are recorded here.

## What this proves

The preflight state of `~/.codex/config.toml` is not sufficient evidence that an already-existing or automatically-restored Desktop Codex thread is using UWA. Desktop routing must be proved per live thread before any long acceptance task is allowed to proceed.

## Current hypotheses

1. Desktop restored an existing conversation created under the official provider and preserved that thread's backend/model state.
2. The Desktop Codex surface may not apply the same provider override semantics as a fresh Codex CLI session for an existing cloud-backed thread.
3. A fresh Desktop thread may still honor UWA, but this has not yet been proved.

Do not select among these hypotheses without route evidence.

## Required next diagnostic

Before retrying D1:

- identify the exact model/reasoning used by the offending Desktop chat from Desktop usage details where available;
- inspect only metadata-level UWA wire evidence for the D1 time window;
- determine whether the offending turn generated any UWA request at all;
- prevent any further long Desktop task until a tiny fresh-thread route probe proves UWA routing without consuming official Codex/Work allowance.

D1 remains `FAIL / ROUTE NOT PROVEN` and M3 remains current.
