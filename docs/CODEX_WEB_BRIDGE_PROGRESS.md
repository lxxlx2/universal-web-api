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
Desktop D5 official restore + harmless task           PASS / LIVE / CLOSED
```

## Current gate

A pre-D1 official-quota event exposed ambiguity between top-level UWA configuration, an existing Desktop conversation's provider state, and the model label rendered in the Desktop UI. The release-critical plan inserted only a narrow Hybrid Routing Safety layer to prevent silent premium-quota use or silent quality downgrade.

Current status:

```text
H0 metadata-only route audit helper                   PASS / CI
H1 exact provider/model/effort fail-closed guard      PASS / CI
H2 tiny fresh Desktop route probe                     PASS / LIVE / CLOSED
H3 explicit official -> UWA stateful handoff          CURRENT; official source PASS; metadata-helper isolation blocker
H4 private metadata-only transition ledger            marker foundation present
H5 synthetic hybrid acceptance                        pending
D1 real Desktop local tool round trip                 PASS / LIVE / CLOSED
D2 same Desktop thread continuation                   PASS / LIVE / CLOSED
D3 full Desktop app restart + history resume          PASS / LIVE / CLOSED
D4 Desktop + UWA restart + same-thread recovery       PASS / LIVE / CLOSED
D5 clean official-account restore + harmless task     PASS / LIVE / CLOSED
Desktop UI D1-D5                                      PASS / LIVE / CLOSED
Medium/High request/page verification                 folded into Desktop/UWA gate
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

D5 first run exposed the lifecycle defect:

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

D5 repaired lifecycle rerun:

```text
T+0   start.py=0 main.py=0 TCP8199=0 pidfile=NO
T+3   start.py=0 main.py=0 TCP8199=0 pidfile=NO
T+10  start.py=0 main.py=0 TCP8199=0 pidfile=NO
T+20  start.py=0 main.py=0 TCP8199=0 pidfile=NO
lifecycle STATUS=STOPPED
provider/model/effort=account defaults
UWA_RESTORE_STATE=ABSENT
working tree=clean
```

D5 final harmless official task after quota became available:

```text
actual Codex Desktop fresh conversation = YES
account-controlled model picker = GPT-6 Astra available
selected reasoning tier = Light
independent checker = OFFICIAL_SOURCE_PASS
OFFICIAL_EFFECT_COUNT = 1
latest route = openai / gpt-6-astra / low
UWA health = unavailable by design
post-marker UWA request/response = 0 / 0
provider=openai route expectation = PASS
```

This closes Desktop D5 and the full Desktop D1-D5 gate. The successful official source effect remains intentionally uncommitted in the synthetic workspace for H3.

The first H3 UWA-side rerun exposed a new acceptance-observability blocker. The controlled ChatGPT browser request was a hidden Codex title/description metadata helper that embedded the H3 source prompt as data and explicitly requested metadata instead of task execution. The corresponding UWA trace completed with no client function calls and no output text, while the synthetic workspace still lacked the UWA continuation effect. This trace is now classified as metadata-helper interference rather than an H3 agent-tool failure.

Recent upstream Codex behavior confirms that Desktop/App metadata helpers are separate background requests and may carry broad agent context and tools. H3 must therefore distinguish metadata helpers from actual agent turns before required-tool detection, web-session affinity and post-marker route counting. The existing imperative-English required-tool detector repair remains relevant for the eventual real H3 agent turn.

H3 next step:

```text
source official effect already present exactly once
→ keep current UWA provider state
→ classify Codex Responses requests as agent_turn vs metadata_helper
→ isolate/short-circuit metadata helpers before required-tool detection and main conversation affinity
→ report helper traffic separately in route/wire audit
→ add redacted regression fixture matching observed title/description helper shape
→ review focused tests and CI
→ rerun one fresh H3 UWA Desktop turn
→ append one UWA continuation effect only from the real agent turn
→ prove official effect count remains exactly one
→ prove UWA effect count exactly one
→ verify uwa / chatgpt / high agent route
```

Detailed records:

- `docs/CODEX_DESKTOP_D1_LIVE_PASS_2026-09-08.md`
- `docs/CODEX_DESKTOP_D2_LIVE_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_D3_LIVE_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_D4_LIVE_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_D5_OFFICIAL_UWA_RESPAWN_FAILURE_2026-09-09.md`
- `docs/CODEX_DESKTOP_D5_LIFECYCLE_RERUN_PASS_2026-09-09.md`
- `docs/CODEX_DESKTOP_D5_LIVE_PASS_2026-09-09.md`
- `docs/CODEX_H3_METADATA_HELPER_INTERFERENCE_2026-09-09.md`
- `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`

## Accelerated release-critical path

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       CURRENT; H0-H2 PASS, H3 metadata-helper isolation blocker
M3b Desktop UI D1-D5                                  PASS / LIVE / CLOSED
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
