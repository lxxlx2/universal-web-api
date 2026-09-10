# Codex Hybrid Routing Safety M3a — LIVE PASS — 2026-09-10

## Result

M3a Hybrid Routing Safety H0-H5 is PASS / LIVE / CLOSED.

The final one-shot acceptance preserved the previously verified official source effect and completed the UWA continuation without duplicating local tool effects.

## H3 final stateful handoff

The preserved synthetic workspace started with exactly:

```text
BASELINE
OFFICIAL_EFFECT_ONCE
```

The official source checker passed before the UWA turn. A fresh UWA Codex agent turn then completed with real client tool activity and produced the final exact state:

```text
BASELINE
OFFICIAL_EFFECT_ONCE
UWA_CONTINUATION_ONCE
```

Acceptance evidence:

```text
Codex exec return code                         0
Codex turn.completed                           YES
real client tool items                         YES
official effect count                          1
UWA continuation effect count                  1
independent handoff checker                     PASS
agent exec_command response                     YES
agent completed response                        YES
agent request model/effort                      chatgpt / high
authoritative latest route                      uwa / chatgpt / high
request-manager running count after             0
browser connected after                         YES
metadata helper excluded from agent accounting  YES
```

This closes H3. The official source half was not rerun.

## H4 private transition ledger

The private metadata-only hybrid ledger was written under the local UWA state directory and verified with private file mode. The final transition records a source route of official Codex and a target route of UWA, using only hashed workspace/session identities in the persisted ledger.

Acceptance evidence:

```text
ledger present             YES
private mode               YES
last event                 complete
source provider/model      openai / gpt-6-astra
target provider/model      uwa / chatgpt
target effort              high
workspace identity         hash only
session identity           hash only
```

No prompt, command body, tool output, raw workspace path, thread id, browser id, PID, cookie or credential is stored in the public repository evidence.

## H5 aggregate synthetic hybrid acceptance

The aggregate gate rechecked the final durable effect state, independent handoff checker and route identity:

```text
official effect count                 1
UWA effect count                      1
handoff checker                       PASS
route                                 uwa / chatgpt / high
no duplicate effect                   YES
H5 synthetic hybrid acceptance        PASS
```

## Classification

```text
H0 route audit                         PASS / CLOSED
H1 route/model/effort guard            PASS / CLOSED
H2 fresh Desktop route probe           PASS / LIVE / CLOSED
H3 official -> UWA stateful handoff    PASS / LIVE / CLOSED
H4 private transition ledger           PASS / CLOSED
H5 synthetic hybrid acceptance         PASS / CLOSED
M3a Hybrid Routing Safety              PASS / LIVE / CLOSED
M3b Desktop D1-D5                      PASS / LIVE / CLOSED
```

The next release-critical gate is M4: one real-project long-task pilot through the verified UWA route.
