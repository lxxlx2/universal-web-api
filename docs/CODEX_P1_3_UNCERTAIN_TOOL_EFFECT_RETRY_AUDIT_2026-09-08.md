# P1.3 uncertain tool-effect reconciliation before retry — audit checkpoint — 2026-09-08

## Audit result

The merge-critical invariant is that UWA must not automatically replay a client tool request after the tool may already have been delivered to Codex and executed locally.

The current V2 architecture already has a narrow safe retry surface:

1. managed UWA provider configuration sets both `request_max_retries = 0` and `stream_max_retries = 0`, disabling Codex provider-level transport replay;
2. V2 strict required-tool repair buffers all non-keepalive Responses events before deciding whether a repair attempt is allowed;
3. if the buffered attempt contains the required real `function_call`, the attempt is satisfied and is delivered to Codex without another automatic model attempt;
4. if the buffered attempt terminates as `response.failed`, the real failure is preserved without retry;
5. only a completed attempt with no required client function call can enter the bounded required-tool repair path. Because its non-comment events were still buffered inside UWA, Codex has not received a client tool call from that attempt and no local tool effect can have occurred through the bridge.

This means strict model repair happens only before a client tool effect becomes possible. Once a real client function call is observable for delivery, automatic repair stops.

## Related continuity guards

Already completed P1.3 hardening adds further protection:

- matching `function_call` + `function_call_output` suppresses duplicate natural-language required-tool enforcement;
- conflicting `call_id -> response_id` identity is fenced instead of rebound;
- conflicting `response_id -> web conversation` identity is rejected;
- lost affinity falls back to persisted reconstructed history or fails closed when no trustworthy history exists.

## Remaining work for this sub-gate

Add focused async regressions proving:

```text
function_call observed            -> no second strict attempt
response.failed observed          -> no second strict attempt
no tool call completed response   -> bounded repair is allowed, but first buffered response is not delivered
```

No new retry framework or effect database is warranted unless those regressions expose a contradiction in the current implementation.
