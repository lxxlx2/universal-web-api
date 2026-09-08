# Codex Web Bridge Progress

## Branches

- stable verified base: `security-hardening`
- active V2 development: `codex-web-bridge-v2`
- V2 Draft PR: #2

## Verified milestones

```text
Stage A-F protocol/CLI acceptance                    PASS
aggregate A-F checker                                PASS
P1.1 legacy Responses compact direct live            PASS
versioned lifecycle/provider switch CI/live          PASS
P1.2 stream/usage + TokenCount                       PASS
P1.2 native auto-compact trigger/local fallback      PASS
P1.2 remote V2 implementation/CI                     PASS
P1.2 UWA provider precondition live                  PASS
P1.2 native remote V2 compaction macOS live          PASS
P1.2 same-thread post-remote recovery                 PASS / CLOSED
P1.3 lost-affinity/restart fallback                   PASS / CLOSED
P1.3 stable identity/stale fencing                    PASS / CLOSED
P1.3 uncertain tool-effect retry safety               PASS / CLOSED
Hybrid H0 metadata route audit                        PASS / CI
Hybrid H1 exact route/model/effort guard              PASS / CI
Hybrid H2 fresh Desktop route probe                   PASS / LIVE / CLOSED
Desktop D1 local tool round trip                      PASS / LIVE / CLOSED
Desktop D2 same-thread continuation                   PASS / LIVE / CLOSED
Desktop D3 Desktop restart + history resume           PASS / LIVE / CLOSED
Desktop D4 Desktop + UWA restart recovery             PASS / LIVE / CLOSED
D5 lifecycle code repair                              PASS / 18 focused tests / CI
```

## Current gate

A pre-D1 official-quota event exposed ambiguity between top-level UWA configuration, an existing Desktop conversation's provider state, and the model label rendered in the Desktop UI. The release-critical plan inserted only a narrow Hybrid Routing Safety layer to prevent silent premium-quota use or silent quality downgrade.

Current status:

```text
H0 metadata-only route audit helper                   PASS / CI
H1 exact provider/model/effort fail-closed guard      PASS / CI
H2 tiny fresh Desktop route probe                     PASS / LIVE / CLOSED
H3 explicit official -> UWA stateful handoff          pending
H4 private metadata-only transition ledger            marker foundation present
H5 synthetic hybrid acceptance                        pending
D1 real Desktop local tool round trip                 PASS / LIVE / CLOSED
D2 same Desktop thread continuation                   PASS / LIVE / CLOSED
D3 full Desktop app restart + history resume          PASS / LIVE / CLOSED
D4 Desktop + UWA restart + same-thread recovery       PASS / LIVE / CLOSED
D5 clean official-account restore                     BLOCKED / repaired live rerun pending
Medium/High request/page verification                 folded into Desktop gate
```

## Desktop evidence

D1:

```text
multi_file: PASS
ACCEPTANCE_PASS
route = uwa / chatgpt / high
real exec_command function calls = YES
```

D2:

```text
CONTEXT_READY
CONTEXT_PASS
context: PASS
ACCEPTANCE_PASS
route = uwa / chatgpt / high
post-marker request/response = 3 / 3
```

D3:

```text
context: PASS
ACCEPTANCE_PASS
session identity before/after Desktop restart = MATCH
route = uwa / chatgpt / high
post-marker request/response = 3 / 3
ROUTE_EXPECTATION_PASS = YES
```

D4:

```text
context: PASS
ACCEPTANCE_PASS
session identity before/after Desktop + UWA boundary = MATCH
route = uwa / chatgpt / high
post-marker request/response = 3 / 3
post-restart exec_command present = YES
completed Responses turn = YES
ROUTE_EXPECTATION_PASS = YES
```

D5 first run:

```text
official config restore = PASS
Memories restore = PASS
authentication preserved = YES
account-default provider/model/effort = PASS
private restore state removed = YES
UWA remains stopped = FAIL
replacement healthy listener appeared on TCP 8199
```

The root cause was confirmed from process ancestry: the old provider-switch stop path killed the active `main.py` listener while leaving the repository-owned `start.py` launcher alive, allowing immediate respawn. Commit `143b396` removes the independent listener-only shutdown semantics and routes provider-switch shutdown through the hardened launcher-aware lifecycle path. Focused provider-switch/lifecycle tests pass 18/18, and the Security hardening GitHub Actions run for `143b396` completed successfully.

The next live gate is a repaired D5 lifecycle rerun from a known healthy UWA state. It must prove that the launcher, listener, TCP 8199 and pidfile stay absent after the official switch. The final harmless official-provider request remains pending while official Codex quota is unavailable.

Detailed records:

- `docs/CODEX_DESKTOP_D1_LIVE_PASS_2026-09-08.md`
- `docs/CODEX_DESKTOP_D2_LIVE_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_D3_LIVE_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_D4_LIVE_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_D5_OFFICIAL_UWA_RESPAWN_FAILURE_2026-09-09.md`
- `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`

## Accelerated release-critical path

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       CURRENT; H0-H2 PASS
M3b Desktop UI D1-D5                                  CURRENT; D1-D4 PASS, D5 live rerun pending
M4 one real-project long-task pilot
M5 final A-F + compaction + restart regression
M6 CI green + public-repo safety + docs/provenance/license
M7 branch-topology inspection + merge verified V2 to main
```

Broad P2-P5 framework expansion, generalized automatic routing, dashboards and unrelated generic upstream cleanup remain post-main unless a remaining live gate demonstrates a concrete blocker.

## Post-main standalone plan

After verified V2 is merged to `main`:

```text
S1 dependency/import/runtime audit + core manifest
S2 create clearer standalone attributed repository
S3 rerun full CI + CLI/Desktop/live parity acceptance
S4 publish first standalone research release
```

The standalone extraction keeps genuinely required upstream runtime and preserves AGPL-3.0 plus explicit attribution while removing unrelated generic fork surface.

## Recording discipline

Every live result, failure, repair and disruptive checkpoint is committed before the next step. README, canonical current state, this file, Desktop acceptance and the Draft PR should stay aligned as closely as practical. Public records contain only non-sensitive acceptance evidence and omit real account, thread, process, browser and private trace identifiers.
