# Codex Hybrid H2 fresh-route probe PASS — 2026-09-08

## Classification

H2 is PASS.

A fresh Codex Desktop thread was started after the managed UWA mode restart and a route-audit marker was written immediately before the probe turn. The probe completed successfully and the metadata-only post-marker audit proved the new Desktop request used the intended UWA route.

## Sanitized live evidence

```text
CONFIGURED_PROVIDER=uwa
CONFIGURED_MODEL=chatgpt
CONFIGURED_EFFORT=high
LATEST_SESSION_PROVIDER=uwa
LATEST_SESSION_MODEL=chatgpt
LATEST_SESSION_EFFORT=high
CONFIG_SESSION_ROUTE=MATCH
UWA_HEALTH=healthy
UWA_BROWSER_CONNECTED=YES
UWA_WIRE_REQUEST_COUNT=1
UWA_WIRE_RESPONSE_COUNT=1
UWA_WIRE_LATEST_MODEL=chatgpt
UWA_WIRE_LATEST_EFFORT=high
UWA_WIRE_LATEST_STATUS=completed
ROUTE_EXPECTATION_PASS=YES
ROUTE_EXPECTATION_FAILURES=NONE
```

Raw thread identifiers, local paths, marker timestamps, prompt bodies, account information, request bodies and trace filenames are intentionally excluded.

## What this proves

The fresh Desktop route can honor the managed UWA configuration and complete through `uwa / chatgpt / high` with real post-marker UWA wire activity. This closes the release-critical ambiguity introduced by the earlier pre-D1 official-quota event for fresh threads.

Existing old Desktop threads may still carry or reconstruct their own official provider/model state, so they remain unsafe as route evidence. Long Desktop work must continue to use explicit route checks and fresh-thread proof where required.

## Gate transition

```text
H0 metadata-only route audit                  PASS
H1 exact route/model/effort guard             PASS
H2 fresh Desktop route probe                  PASS / CLOSED
H3 explicit official -> UWA handoff           pending
H4 private transition ledger                  foundation present
H5 synthetic hybrid acceptance                pending
D1 real Desktop local-tool round trip         READY / CURRENT
```

The project returns to the original Desktop acceptance path at D1. H3-H5 remain release-critical before `main`, but they no longer block starting D1.
