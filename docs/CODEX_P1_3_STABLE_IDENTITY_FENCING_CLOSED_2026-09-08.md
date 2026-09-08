# P1.3 stable continuation identity / stale-generation fencing — CLOSED — 2026-09-08

This merge-critical P1.3 sub-gate is closed after focused identity fencing and complete CI.

## Stable response identity

`app/services/codex_web_session_affinity.py` now treats one response id as immutable affinity identity:

```text
first response_id -> pathname/model/reasoning binding       accept
identical repeated binding                                  accept / refresh
same response_id with different path/model/reasoning        reject without overwrite
```

A late or stale attempt therefore cannot silently move an existing response id to another ChatGPT conversation.

## Stable call identity

`app/services/codex_v2_runtime_hardening.py` now treats one function call id as stable continuation identity:

```text
first call_id -> response_id mapping                 accept
same call_id + same response_id                      accept / refresh
same call_id + different response_id                 fence as conflicted
```

A conflicted call id no longer resolves through process-local affinity. Normal Responses hydration / restart fallback must establish continuity instead of guessing which web conversation owns the tool result. Conflict state is bounded by the existing process-local TTL/capacity pruning.

This is intentionally fail-closed and does not persist prompt, command, tool output, browser path, or credentials.

## Regression coverage

`tests/test_codex_continuation_identity_fencing.py` covers:

- identical call-id replay remains stable;
- conflicting call-id/response-id mapping becomes non-resolvable;
- a conflicted id fences multi-output affinity resolution;
- identical response-affinity rebind is accepted;
- conflicting pathname is rejected without overwriting the original binding;
- conflicting model/reasoning is rejected.

## CI

Security hardening workflow run #483 completed successfully across public-repo safety, Ubuntu/macOS Python 3.11/3.13 security jobs, and the reproducible upstream regression suite.

## Gate decision

P1.3 sub-gate `stable continuation identity / stale-generation fencing` is **PASS / CLOSED**.

Next merge-critical sub-gate: uncertain tool-effect reconciliation before retry.
