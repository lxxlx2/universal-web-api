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
ChatGPT idle-composer send repair                     PASS / LIVE / CLOSED
H3 required client-tool path                          PASS / LIVE / CLOSED
H3 metadata-helper isolation                          PASS / LIVE / CLOSED
Desktop D1 local tool round trip                      PASS / LIVE / CLOSED
Desktop D2 same-thread continuation                   PASS / LIVE / CLOSED
Desktop D3 Desktop restart + history resume           PASS / LIVE / CLOSED
Desktop D4 Desktop + UWA restart recovery             PASS / LIVE / CLOSED
Desktop D5 official restore + harmless task           PASS / LIVE / CLOSED
```

## Current gate

Hybrid H3 is at its final synthetic handoff acceptance. The official source half is already accepted and remains preserved exactly once. Do not rerun the official source action.

Three UWA-side blockers encountered during H3 are closed:

```text
ChatGPT idle composer falsely treated as streaming   CLOSED / 1dac853 / direct High live PASS
required exec_command wording missed by detector     CLOSED / 38ede75 / real client tool live PASS
hidden Codex metadata helper polluted agent lane      CLOSED / de875e4 / local isolation live PASS
```

The required-tool live probe proved the real Codex request carried `exec_command`, `required_tool=exec_command` was selected, the bounded repair emitted a genuine `exec_command` function call, Codex executed it locally, a matching `function_call_output` returned, the final Responses turn completed, and request-manager running count returned to zero.

The metadata-helper live probe then proved a current-Codex hidden title request is classified before required-tool logic. It completed locally with a bounded structured title, emitted no client function call, did not consume the ChatGPT Web coding lane, produced only `request_kind=metadata_helper` trace records, was excluded from route-audit agent traffic, and left zero running requests.

Security hardening CI for the metadata-helper implementation commit completed successfully.

## H3 final closure requirements

The preserved synthetic handoff workspace must prove in one fresh UWA Codex agent turn:

```text
official source effect count = 1
UWA continuation effect count = 1
independent handoff checker = PASS
real required exec_command call = YES
metadata helper excluded from agent accounting = YES
agent request = chatgpt / high
authoritative route = uwa / chatgpt / high
running request count after completion = 0
```

The one-shot live helper is `tools/codex_h3_final_handoff_live.py`. It never reruns the official source action and does not print prompt bodies, command bodies, tool output, raw thread/browser/process identifiers, cookies or credentials.

## Desktop evidence

```text
D1 real local tool execution                         PASS / LIVE / CLOSED
D2 same-thread context continuity                    PASS / LIVE / CLOSED
D3 Desktop restart + history resume                  PASS / LIVE / CLOSED
D4 Desktop + UWA restart + same-thread recovery      PASS / LIVE / CLOSED
D5 official provider restore + harmless task         PASS / LIVE / CLOSED
Desktop UI D1-D5                                     PASS / LIVE / CLOSED
```

D5 created the preserved official source effect on authoritative `openai / gpt-6-astra / low` metadata with UWA unavailable by design. This source state is the starting point for H3 and must remain exactly once.

## Accelerated release-critical path

```text
M1 P1.2 same-thread post-remote recovery              PASS / CLOSED
M2 P1.3 minimal continuity blockers                   PASS / CLOSED
M3a Hybrid Routing Safety H0-H5                       CURRENT; H3 final live acceptance next
M3b Desktop UI D1-D5                                  PASS / LIVE / CLOSED
M4 one real-project long-task pilot                   pending
M5 final A-F + compaction + restart regression        pending
M6 CI green + public-repo safety + docs/provenance    pending
M7 branch-topology inspection + merge to main         pending
```

After H3 closes, finish H4 private metadata-only transition ledger and H5 synthetic hybrid acceptance, then advance to M4.

## Post-main standalone plan

After verified V2 is merged to `main`:

```text
S1 dependency/import/runtime audit + core manifest
S2 create clearer standalone attributed repository
S3 rerun full CI + CLI/Desktop/live parity acceptance
S4 publish first standalone research release
```

The standalone extraction keeps genuinely required upstream runtime and preserves AGPL-3.0 plus explicit attribution while removing unrelated generic fork surface only after dependency proof.

## Current records

- `docs/CODEX_H3_REQUIRED_TOOL_REPAIR_LIVE_PASS_2026-09-10.md`
- `docs/CODEX_H3_METADATA_HELPER_ISOLATION_LIVE_PASS_2026-09-10.md`
- `docs/CODEX_H3_FINAL_HANDOFF_LIVE_GATE_2026-09-10.md`
- `docs/CODEX_DIRECT_HIGH_BROWSER_STALL_2026-09-09.md`
- `docs/CODEX_DESKTOP_D5_LIVE_PASS_2026-09-09.md`
- `docs/CODEX_HYBRID_ROUTING_SAFETY_2026-09-08.md`
- `docs/ACCELERATED_MAIN_MERGE_GATE_2026-09-08.md`

## Recording discipline

Every live result, failure, repair and disruptive checkpoint is committed before the next step. README, canonical current state, this file, Desktop acceptance and the Draft PR should stay aligned as closely as practical. Public records contain only non-sensitive acceptance evidence and omit real account, thread, process, browser and private trace identifiers.
