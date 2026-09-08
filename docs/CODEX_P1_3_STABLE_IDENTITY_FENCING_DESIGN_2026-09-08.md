# P1.3 stable continuation identity / stale-generation fencing — design checkpoint — 2026-09-08

## Audit result

Codex response ids are generated internally from current time plus random UUID material, so ordinary response creation already has a strong unique identity. The minimal merge-critical stale-identity risk is in the process-local continuation metadata bridges, not in the private persisted history schema.

Two mutable mappings can currently be reassigned:

1. runtime hardening stores `call_id -> response_id` metadata and currently overwrites an existing call id unconditionally;
2. web-session affinity stores `response_id -> ChatGPT conversation pathname` and currently overwrites an existing response id unconditionally.

A replayed/late attempt that reuses an existing call id with a different response id could therefore redirect subsequent `function_call_output` continuation to the wrong web conversation. Likewise, rebinding one response id to a different pathname/model/reasoning would violate stable response identity.

## Minimal fencing contract

`call_id -> response_id`:

```text
first mapping                         accept
same call_id + same response_id       accept / refresh
same call_id + different response_id  mark conflicted and do not resolve through affinity
```

A conflicted call id stays fenced until the bounded process-local TTL prunes it. Falling back to normal Responses hydration is safer than guessing which web conversation owns the tool result.

`response_id -> web conversation`:

```text
first binding                                      accept
identical repeated binding                         accept / refresh
same response_id with different path/model/reasoning  reject without overwriting prior binding
```

## Scope

This is intentionally narrow. No database generation migration, broad concurrency architecture, browser lease framework, or distributed transaction layer is required for the current merge-critical identity invariant.

Next action: implement these two immutable-identity guards with focused regressions, then run the full security-hardening CI.
