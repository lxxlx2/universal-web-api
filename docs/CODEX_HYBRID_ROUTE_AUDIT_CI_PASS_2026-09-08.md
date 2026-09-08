# Hybrid route-audit CI pass — 2026-09-08

## Result

The first release-critical Hybrid Routing Safety implementation block is green.

`tools/codex_route_audit.py` provides metadata-only route auditing for configured Codex state, recent authoritative Codex session metadata, UWA health, and UWA metadata wire activity.

## Safety / semantics

The helper:

- reads configured provider/model/reasoning from `~/.codex/config.toml`;
- reads only authoritative Codex `session_meta`, `turn_context`, and explicit thread-settings metadata;
- does not recursively search arbitrary rollout content, so historical model/reasoning strings cannot masquerade as the active route;
- prints only provider/model/effort, age, a hashed local session identity, health, and aggregate UWA wire metadata;
- never prints raw rollout paths, thread ids, prompts, source code, command bodies, tool output, cookies or credentials;
- creates private `0600` markers under `~/.uwa`;
- requires a real UWA wire request after the marker before an expected `provider=uwa` route can PASS;
- supports exact expected provider/model/effort checks and fails closed on mismatch.

The exact expectation mechanism is the minimal first-release quality guard: if a task requires a specific route/model/reasoning tier, the long task must not start unless a tiny route probe proves those exact values.

## CI

Security hardening run `34247199970` completed successfully after fixing a Python 3.13-only dynamic test loader issue.

```text
public-repo-safety                  PASS
security Ubuntu 3.11               PASS
security Ubuntu 3.13               PASS
security macOS 3.11                PASS
security macOS 3.13                PASS
upstream reproducible regression   PASS
```

## Gate status

```text
H0 metadata-only route audit helper                  PASS / CI
H1 exact route/model/effort fail-closed guard        PASS / CI
H2 fresh Desktop route probe                         CURRENT / live pending
H3 official -> UWA stateful handoff                  pending
H4 private transition ledger                         marker foundation present / pending
H5 hybrid live acceptance                            pending
```

Next action is a read-only local status run, then a tiny fresh Desktop route probe. Do not run the full D1 workload until H2 proves the intended route.
