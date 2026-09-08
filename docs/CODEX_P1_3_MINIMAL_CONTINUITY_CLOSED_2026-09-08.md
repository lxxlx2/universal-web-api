# P1.3 minimal continuity hardening — CLOSED — 2026-09-08

The accelerated merge-critical P1.3 gate is closed. All three intentionally narrow correctness blockers are PASS.

## 1. Lost-affinity / UWA-restart fallback correctness — PASS

Live Stage F already proved a real UWA restart with process-local web affinity cleared, same Codex thread recovery, conversation-only context recovery, real local tool execution and an independent checker PASS.

Focused regression now locks the implementation fallback hierarchy:

```text
healthy affinity
-> same ChatGPT conversation + delta

lost affinity + persisted previous_response history
-> fresh ChatGPT conversation + reconstructed full history

no trustworthy continuation source
-> fail closed
```

Closure record: `docs/CODEX_P1_3_LOST_AFFINITY_RESTART_FALLBACK_CLOSED_2026-09-08.md`.

## 2. Stable continuation identity / stale-generation fencing — PASS

Stable identity is enforced for both continuation metadata bridges:

```text
response_id -> web conversation
same identity replay                 accepted
conflicting path/model/reasoning     rejected without overwrite

call_id -> response_id
same identity replay                 accepted
conflicting response id              fenced; affinity resolution disabled
```

A conflicted call id falls back to normal trustworthy hydration instead of guessing which web conversation owns a tool result.

Closure record: `docs/CODEX_P1_3_STABLE_IDENTITY_FENCING_CLOSED_2026-09-08.md`.

## 3. Uncertain tool-effect reconciliation before retry — PASS

Automatic repair is allowed only before a client tool effect becomes possible:

```text
real function_call observed     -> no automatic retry
response.failed                 -> no automatic retry
no-tool completed attempt       -> may bounded-repair while response is still buffered inside UWA
provider transport retries      -> disabled
```

Closure record: `docs/CODEX_P1_3_UNCERTAIN_TOOL_EFFECT_RETRY_CLOSED_2026-09-08.md`.

## CI

Relevant complete workflow runs:

- #478: lost-affinity fallback regression — PASS
- #483: stable identity fencing — PASS
- #486: uncertain tool-effect retry safety — PASS

Each completed public-repo safety, Ubuntu/macOS Python 3.11/3.13 security jobs, and the reproducible upstream regression suite.

## Gate decision

P1.3 / merge-critical M2 is **PASS / CLOSED**.

The release-critical path advances to M3: Codex Desktop UI D1-D5 with Medium/High reasoning end-to-end verification folded into the Desktop gate.
