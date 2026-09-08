# Codex Hybrid Routing Safety — 2026-09-08

## Product goal

The preferred operating mode is hybrid, but routing must never be silent:

```text
official Codex available and intentionally selected
→ use the official provider / selected official model
→ consume official Codex/Work allowance knowingly

when official allowance is exhausted, unavailable, or the operator explicitly switches
→ hand off to the UWA-backed ChatGPT Web route
→ continue from the same local workspace/state with an auditable handoff
```

The user must be able to tell which provider/model/reasoning tier is about to run before a long task starts. The bridge must not silently spend premium official allowance, and it must not silently downgrade a task that requires a stronger model.

## Why this became release-critical

A pre-D1 live event proved that an existing Desktop Codex conversation can resume as `provider=openai`, `model=gpt-6-astra`, `effort=ultra` even though separate UWA-backed sessions existed earlier and the local Codex config had been switched to UWA. The existing official conversation consumed the refreshed official allowance.

This is not a D1 failure, but it proves that config state alone is not sufficient user-facing routing evidence. A release that lets users unknowingly consume official premium quota would be unsafe and confusing.

Detailed event record: `docs/CODEX_DESKTOP_D1_OFFICIAL_QUOTA_MISROUTE_2026-09-08.md`.

## Current capability assessment

```text
official provider mode                              YES
UWA provider mode                                   YES
manual official <-> UWA switch                      YES
exact restore of UWA-owned config overrides         YES
local session provider/model/effort metadata         YES
UWA wire metadata                                    YES
old Desktop thread provider stickiness observed      YES
per-task route visibility before long work           NO
automatic quota-aware official -> UWA handoff        NO
quality-floor / no-silent-downgrade policy            NO
auditable cross-provider handoff workflow             NO
```

Therefore the ideal hybrid mode is not yet complete.

## Release-scope decision

Keep the accelerated release target. Do not build a broad orchestration platform before `main`.

Add only a narrow merge-critical Hybrid Routing Safety block inside M3. It must be small enough to finish alongside Desktop D1-D5, but strong enough to prevent silent quota spend or silent model downgrade.

Broad autonomous scheduling, generalized multi-provider load balancing, rich quota dashboards, pricing optimization and background route arbitration remain post-main.

## H0 — route identity / audit helper

Add a local-only helper that reports, without printing prompt or source content:

```text
configured_provider
configured_model
configured_effort
latest_session_provider
latest_session_model
latest_session_effort
session_age
uwa_health
uwa_wire_activity_since_marker
route_match / route_mismatch / unknown
```

It must read only metadata from local Codex session JSONL and existing UWA metadata traces. It must never commit or print thread ids, prompts, command bodies, private source, cookies, tokens or full trace paths.

This helper is the authoritative route check for live acceptance and later operator use.

## H1 — explicit route intent and quality floor

The first release supports three explicit intents:

```text
official
  require official provider; no UWA fallback without an explicit handoff

uwa
  require UWA provider; fail/stop if a fresh route probe resolves to official

hybrid
  prefer official when intentionally selected and usable;
  after official exhaustion/unavailability, require an explicit auditable handoff to UWA
```

A task may also declare a minimum quality requirement:

```text
provider requirement: official | uwa | either
minimum model class: optional operator-selected label
minimum reasoning tier: e.g. ultra / high / medium
allow downgrade: yes | no
```

For the first release, quality comparison is policy metadata, not a claim that different model families are numerically equivalent. If the requested minimum cannot be proven, fail closed or ask for explicit operator approval. Never silently substitute a weaker route.

## H2 — fresh-thread route probe before long Desktop work

Before D1-D4 or any real-project pilot, a long Desktop task must be preceded by a tiny fresh-thread route probe.

The probe must be harmless and bounded. PASS requires machine-auditable metadata proving the intended provider/model/effort. If the probe resolves to the wrong provider, stop before the long task.

This prevents the failure mode where an old official thread is mistaken for a UWA thread, or vice versa.

The current zero-official-quota window is especially useful: a fresh thread that is truly UWA-backed should still complete and produce UWA wire metadata, while an official route should fail on quota without consuming another long turn.

## H3 — official exhaustion -> UWA handoff

Do not claim transparent in-place hot switching of an existing Desktop thread until it is actually proven. Existing Desktop threads may retain provider/model state.

The safe first-release handoff is explicit and stateful:

```text
official task stops / quota exhausted
→ record source route metadata locally
→ preserve current workspace and Git diff exactly
→ switch managed config to UWA
→ verify UWA health + fresh-thread route probe
→ start a fresh UWA Codex thread in the same workspace
→ provide a local-only handoff prompt/checkpoint
→ continue without repeating or reverting already-applied local tool effects
```

The handoff checkpoint may contain private task context locally because it is meant for the next model session, but it must never be committed to the public repository. Public Git records only non-sensitive metadata/result classifications.

For coding tasks, the handoff should anchor on durable local state first:

- workspace path
- Git status / changed-file list
- current diff
- tests already run and their status when available
- latest user task / latest assistant progress when safely available from local session history

The new model must inspect the current workspace rather than blindly replaying old tool effects.

## H4 — transition ledger

Maintain a private metadata-only route ledger under `~/.uwa`, recording transitions such as:

```text
timestamp
source provider/model/effort
target provider/model/effort
event: probe | start | quota_exhausted | handoff | switch | complete
session identity hash only, never raw thread id
workspace hash/name only as needed, no source content
```

The user-facing status command should make transitions easy to understand:

```text
LAST_ROUTE=openai / gpt-6-astra / ultra
CURRENT_CONFIG=uwa / chatgpt / high
STATE=ROUTE_MISMATCH_OLD_THREAD
RECOMMENDATION=START_FRESH_UWA_THREAD_OR_EXPLICITLY_CONTINUE_OFFICIAL
```

## H5 — acceptance before main

Hybrid Routing Safety is merge-critical only at this minimal level.

Required before `main`:

```text
H0 route-audit helper + tests                         PASS
H1 explicit route intent / fail-closed quality guard PASS
H2 fresh Desktop route probe                         LIVE PASS
H3 official->UWA handoff on synthetic workspace      LIVE PASS
H4 private transition ledger                         PASS
D1-D5 Desktop acceptance using route checks          PASS
```

The official->UWA handoff test may use a synthetic task and a simulated/actual quota-exhausted official state. It must prove no duplicate local tool effect and no silent provider downgrade.

## What remains post-main

```text
fully automatic quota polling from unsupported/private UI internals
background automatic thread migration
provider cost optimization
multi-provider ranking/scoring
generalized policy engine
rich UI/dashboard
automatic model benchmarking and task classifier
```

If OpenAI exposes a stable supported quota/status API later, `hybrid` can become more automatic. Until then, unknown quota state must not be guessed.

## Updated release path

```text
M1 P1.2 remote compaction recovery              PASS / CLOSED
M2 P1.3 minimal continuity                      PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                 CURRENT / release-critical
M3b Desktop D1-D5 + reasoning verification      CURRENT after route probe
M4 real-project long-task pilot                 pending
M5 final regressions                            pending
M6 CI / safety / docs / provenance              pending
M7 topology inspection + merge to main          pending
```

This does not change the fast-release strategy. It adds one narrow safety layer because the live Desktop behavior showed that routing ambiguity can directly consume scarce official allowance or silently use the wrong model tier.
