# P1.3 uncertain tool-effect reconciliation before retry — CLOSED — 2026-09-08

This merge-critical P1.3 sub-gate is closed after audit, focused retry-safety regressions, and complete CI.

## Safety invariant

UWA must never automatically replay a client tool request after that tool may already have been delivered to Codex and executed locally.

The V2 strict required-tool path now has regression coverage for the existing safety contract:

```text
required real function_call observed
-> strict attempt is satisfied
-> response is delivered to Codex
-> no second automatic strict attempt

response.failed observed
-> real terminal failure is preserved
-> no automatic strict retry

completed attempt with no required tool call
-> non-comment events remain buffered inside UWA
-> Codex has not received a client tool from that attempt
-> bounded repair retry is allowed
-> buffered first attempt is not delivered
```

Managed UWA provider configuration also sets `request_max_retries = 0` and `stream_max_retries = 0`, so provider-level transport replay cannot silently duplicate a possibly delivered client tool call.

## Related reconciliation guards

The broader P1.3 continuity work also guarantees:

- matching `function_call` + `function_call_output` prevents duplicate natural-language required-tool enforcement;
- conflicting call-id continuation identity is fenced;
- conflicting response-id web-affinity identity is rejected;
- lost affinity uses trustworthy reconstructed history or fails closed.

## Regression coverage

`tests/test_codex_uncertain_tool_effect_retry.py` proves:

- observed client function call stops automatic strict retry;
- terminal failure stops automatic strict retry;
- a no-tool attempt can retry only while its effect-capable events remain buffered and undisclosed to the client.

## CI

Security hardening workflow run #486 completed successfully across public-repo safety, Ubuntu/macOS Python 3.11/3.13 security jobs, and the reproducible upstream regression suite.

## Gate decision

P1.3 sub-gate `uncertain tool-effect reconciliation before retry` is **PASS / CLOSED**.
