# P1.2 auto-compact trigger live PASS — 2026-09-08

## Scope

Real macOS validation of the versioned small-step auto-compaction trigger probe after the second large-context attempt was diagnosed as a threshold-crossing defect in the acceptance strategy.

## Environment

```text
Codex CLI                    0.153.4
UWA service                  healthy
controlled browser           connected
model context window         64000
auto-compact threshold       57600
hard effective context cap   60800
```

No provider identity change or UWA restart was required for this probe.

## Safe live evidence

The probe grew the same Codex thread using coarse filler, then switched to small filler near the threshold:

```text
active last tokens
14205
21122
28039
34956
41873
48790
55707
56568
57429
58290
```

The decisive transition was:

```text
57429 < 57600
58290 > 57600
```

The successful over-threshold turn remained below the hard effective cap:

```text
PRE_TRIGGER_ACTIVE_TOKENS=58290
PRE_TRIGGER_OVER_HARD_CAP=NO
```

Before the tiny trigger there was no compact lifecycle marker. On the next tiny turn Codex observed the persisted over-threshold state and compacted before ordinary sampling:

```text
PRE_TRIGGER_ROLLOUT_COMPACT_MARKERS=0
TRIGGER_REPLY_EXACT=YES
TRIGGER_TOOL_EFFECTS=0
ROLLOUT_COMPACT_MARKER_DELTA=1
```

The current custom UWA provider did not call the remote compact endpoint:

```text
REMOTE_COMPACT_ROUTE_DELTA=0
REMOTE_COMPACT_SUCCESS_DELTA=0
AUTO_COMPACT_MODE=LOCAL_FALLBACK
```

No synthetic token was written into the acceptance workspace:

```text
TOKEN_LEAK_WORKSPACE=NO
```

Final gate:

```text
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

## Interpretation

This live pass proves the following Codex 0.153.4 behavior under UWA:

1. fallback Responses usage reaches Codex with usable non-zero counts;
2. `TokenCount` state persists across resumed CLI processes;
3. the native 57,600-token auto-compact threshold is respected when the previous successful turn is already over threshold;
4. the next tiny turn triggers Codex pre-turn compaction;
5. under the normal `Universal Web API` custom provider identity, Codex selects its local fallback compaction path;
6. the earlier second-attempt failure was caused by the acceptance runner jumping across the threshold after the pre-turn compact check, not by a broken native trigger.

## Remaining P1.2 blocker

Remote compact protocol support remains a separate compatibility gate. Direct UWA `POST /v1/responses/compact` is already live-PASS from P1.1, but Codex 0.153.4 classifies the current custom provider as `RemoteCompactionSupport::Unsupported` and therefore does not select that endpoint automatically.

The next step is to establish the narrowest safe provider capability mechanism that enables remote compaction without enabling unrelated OpenAI-specific behavior. Do not rename the provider to `OpenAI` blindly. Inspect the exact 0.153.4 provider capability classifier and all relevant Azure/provider-name branches first.

## Public repository safety

This record intentionally excludes the private Codex thread identifier, rollout path/name, browser identifiers, live process identifiers, prompts, response bodies, raw traces and private UWA logs.
