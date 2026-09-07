# WebCodex architecture review — 2026-09-07

## Scope

This review evaluates `yyjeqhc/webcodex` as a design reference for `codex-web-bridge-v2`.

Reviewed upstream state:

```text
repository: yyjeqhc/webcodex
branch: main
commit: 5a4da8fff7a7a7dc52bd963e8dc22ef530160f28
review date: 2026-09-07
license: Apache-2.0
```

Primary materials reviewed:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/RUNNER.md`
- `docs/MCP.md`
- `docs/CODING_WORKFLOW.md`
- `docs/agent/job-reliability-and-concurrency.md`
- `docs/agent/session-model.md`
- `docs/architecture/durable-agent-runtime.md`
- `docs/agent/tool-request-tracing.md`
- `docs/TESTING.md`
- `SECURITY.md`
- `crates/webcodex-core/src/job_observation.rs`

This is a design study. No WebCodex source file is copied into this repository by this review.

## Executive conclusion

WebCodex is highly relevant to the later reliability phases of V2, but it should **not** replace the current architecture.

The two projects solve different core problems:

```text
UWA Codex Web Bridge V2
official Codex Desktop / CLI remains local executor
        ↓
UWA translates/guards Responses and browser-Web inference
        ↓
ChatGPT Web chooses client tools
        ↓
Codex owns filesystem/shell/test/Git/sandbox/approval

WebCodex
AI/MCP client
        ↓
WebCodex Server
        ↓
WebCodex Runner
        ↓
Runner owns filesystem/shell/test/Git/job execution
```

Replacing Codex with a WebCodex-style Runner would duplicate the executor, sandbox and lifecycle responsibilities we intentionally keep inside official Codex. It would also weaken the primary product goal: normal use from official Codex Desktop / CLI while inference is bridged through UWA.

The correct use of WebCodex is as a reference for **continuity semantics, uncertain-effect handling, process identity, concurrency, MCP contracts, bounded diagnostics and acceptance design**.

## What validates the current V2 direction

### 1. The online model must not become filesystem authority

WebCodex explicitly keeps the Server away from filesystem discovery and makes the local Runner authoritative for registered Projects. The online model sees tool results, not arbitrary host filesystem access.

That strongly supports the V2 decision already made during Stage E:

- ChatGPT Web/browser-visible filesystem state is not authoritative;
- Codex's declared client tools and native workspace are authoritative for local execution availability;
- a browser-model refusal claiming the local workspace is unavailable is invalid until the client tool path has actually been exercised.

No new Runner/project-registry layer should be added to UWA merely to copy this pattern. Codex already supplies the local authority boundary.

### 2. Browser/window continuity is not task identity

WebCodex repeatedly separates durable task/session identities from browser windows, MCP connections and credentials. Window identity may assist adapter-local continuity, but it does not become Workflow Session identity, execution authority or durable work identity.

V2 should formalize the same distinction:

| V2 identity | Meaning | Must not be treated as |
| --- | --- | --- |
| Codex thread | user-visible task/conversation continuity | web conversation pathname or UWA process identity |
| Responses `response_id` | protocol snapshot/continuation identity | authorization or local execution identity |
| Responses `call_id` | one client-tool call correlation identity | task identity, retry permission or authority |
| ChatGPT `/c/...` path | browser transport affinity optimization | durable task truth |
| UWA process instance | one running bridge generation | durable Codex thread identity |
| controlled browser/tab binding | current web transport target | local workspace/execution authority |
| local command/process state | Codex-owned executor state | UWA-owned Job identity |

This distinction is already implicit in the current four-layer continuity design. P1.3 should make it an explicit tested contract.

## Highest-value WebCodex lessons for V2

### A. Request loss is not execution loss

This is the most important lesson for P1.3/P2.

WebCodex treats an HTTP/MCP request, a Job execution and an observation cursor as different lifetime domains. If a transport request disappears after execution may have started, it does not automatically retry the command. It first reconciles the authoritative execution state.

V2 has an analogous risk around client tool calls:

```text
ChatGPT Web chooses function_call
        ↓
Codex may execute local effect
        ↓
network / browser / UWA continuation fails
        ↓
bridge must not blindly ask for / replay another equivalent effect
```

Current duplicate-required-tool suppression is useful but narrower than this problem.

Roadmap change:

- P1.3 must include an explicit **uncertain tool-effect recovery** scenario.
- A lost continuation after a `function_call` or after `function_call_output` delivery must be classified separately from a definitely-not-started call.
- Hidden automatic retry of a possibly executed effect must be prohibited.
- Recovery should reuse persisted Responses/Codex history and reconcile the exact call/result state before another effect can be requested.

### B. Stable identity and process generation must be separate

WebCodex separates stable `client_id` from the currently live Runner process/lease. A replacement Runner process cannot submit results as the old process.

The stale-UWA incident we just fixed is the same class of engineering problem at a smaller scale.

V2 should add bounded runtime generation facts:

- one UWA process instance id / start identity;
- Git/build identity for the code actually serving requests;
- browser/controlled-tab generation where useful;
- affinity bindings should be process/generation scoped;
- diagnostics should make it immediately obvious whether a response came from an old process or current checkout.

This does not need to block P1.2. It belongs in the P1.3/lifecycle diagnostic hardening and P5 operator/release evidence.

### C. Correlation identifiers are not authority or retry keys

WebCodex is unusually disciplined about this. Job observation tokens, trace ids, window ids and session correlation ids are explicitly described as observation/correlation state rather than authority, business identity or retry permission.

V2 should document and test the same invariant for:

- `response_id`;
- `call_id`;
- web-session affinity keys;
- private trace correlation ids;
- future browser-generation ids.

A matching identifier can prove correlation. It cannot by itself prove that a local effect should be executed again.

### D. Bounded observation and delta recovery

WebCodex Jobs use bounded stdout/stderr tails and opaque observation tokens containing epoch/revision/cursor state. When continuity cannot be proved, observation returns a bounded reset baseline rather than pretending no output was missed.

V2 should **not** implement its own Job system because Codex owns the local process. However the pattern is useful for:

- bounded UWA diagnostic/event history;
- browser/affinity status snapshots;
- future long trace inspection;
- avoiding giant transcript/debug payloads in P4.

For local command output itself, Codex remains authoritative; UWA must not invent a parallel job/output cursor model.

### E. Fail closed on compatibility ambiguity

WebCodex treats Server/Runner protocol features as capabilities and fails closed when an older compatible peer lacks a required capability. It also rejects ambiguous legacy/current config combinations instead of guessing precedence.

V2 should apply this to Codex protocol drift:

- `/v1/responses` support;
- `/v1/responses/compact` support;
- Responses/SSE item shapes;
- model catalog behavior;
- tool namespace/schema features;
- client-version-specific optional fields.

Roadmap change:

- P2/P5 should add a machine-readable Codex compatibility/capability preflight rather than relying only on ad-hoc runtime symptoms.
- Unsupported protocol features should fail explicitly rather than be silently translated into a semantically different behavior.

### F. Tool descriptions and schemas are part of reliability

WebCodex explicitly treats model-facing tool descriptions as a reliability contract: a long-running operation must tell the model it is the same execution, queued work must not be re-created, and uncertain effects must not encourage blind retries.

For V2, the tools are declared by Codex rather than invented by UWA, so UWA should not rewrite the tool catalog casually. But V2 policy/prompt framing should preserve these semantic facts:

- declared client tools are authoritative;
- an existing call/result pair should be continued, not regenerated;
- transport failure is not proof of tool non-execution;
- local workspace authority belongs to Codex;
- unsupported tool shapes fail visibly.

### G. Structured evidence beats assistant prose

WebCodex has separate review/hygiene/validation evidence and explicitly warns that passing tests or assistant prose do not replace diff/workspace evidence.

This aligns with the existing V2 acceptance discipline and supports keeping it:

- machine checker after every live scenario;
- exact local artifact checks;
- process identity checks for restart tests;
- Git checkpoint before moving on;
- Desktop screenshots alone are not sufficient evidence.

## Areas where WebCodex should influence the roadmap

### P1.2 large-context compaction / recovery

**Keep the existing plan. Do not replace it with WebCodex-style task persistence.**

WebCodex solves durable execution/task state; that is not the same as model context-window compaction. P1.2 must still exercise native Codex `/v1/responses/compact`, generate enough synthetic conversation pressure, observe an actual compaction boundary when possible, and verify recovery of earlier durable facts afterward.

WebCodex contributes one useful rule here: model/context continuity evidence should not be inferred from a browser window or transport connection.

### P1.3 lost-affinity / restart recovery

Expand P1.3 with three explicit contracts inspired by WebCodex:

1. **identity separation** — Codex thread, Responses snapshot, web affinity and UWA process generation remain distinct;
2. **uncertain effect** — if a tool effect may already have executed when continuation is lost, no hidden re-execution occurs;
3. **generation fencing** — stale browser/process affinity state cannot submit or reattach as current state; recovery either uses the exact current binding or reconstructs from persisted history.

Suggested synthetic cases:

```text
function_call emitted -> continuation transport lost -> recover -> same effect exactly once
function_call_output accepted -> response lost -> recover -> no duplicate tool request
UWA restart -> old affinity gone -> persisted history reconstructs -> same Codex thread continues
controlled tab replaced -> stale binding rejected/rebuilt -> no cross-thread leakage
```

### P1.4 real-project long-task pilot

Keep Codex as executor. Borrow WebCodex's acceptance philosophy:

- run on a dedicated branch/worktree;
- inspect before edit;
- require focused validation;
- require diff review;
- preserve unrelated dirty work;
- capture bounded final evidence rather than relying on final prose.

Do not add a second WebCodex-style managed worktree/task-acceptance engine inside UWA.

### P2 concurrency / queue / controlled-tab hardening

WebCodex is especially valuable here.

Add these acceptance requirements:

- serialize requests that target the same logical Codex/Responses continuation when mutation ordering matters;
- keep concurrency planes distinct: request queue, browser tab pool, model request, and Codex local execution are not one shared state;
- queued/blocked continuation keeps the same logical work identity;
- a timeout does not create a replacement effect until prior outcome is reconciled;
- stale process/tab generation cannot publish a late result into a newer continuation;
- bounded status should expose current running/queued counts without leaking payloads.

### P3 MCP / plugin namespace / multi-agent

WebCodex should become a primary reference, but the V2 responsibility boundary remains different.

Adopt conceptually:

- strict structured tool schemas;
- namespace/capability negotiation;
- fail-closed unsupported shapes;
- explicit distinction between correlation, authority and execution identity;
- environment/credential least privilege when external tool providers are involved;
- no implicit task/session identity from a connection or credential.

Do not adopt by default:

- a UWA-hosted local MCP provider process manager;
- a second local Runner;
- durable Agent scheduler/swarm infrastructure.

Official Codex already owns local MCP/tool execution. P3 should first prove that UWA preserves Codex tool namespaces, schemas, call ids and fan-out semantics correctly.

If a future product requirement introduces non-Codex clients, WebCodex's Server/Runner/MCP model can be reconsidered as an optional separate surface rather than changing the V2 core.

### P4 SSE slimming / transcript hygiene

Borrow the bounded-evidence principle, not the Job implementation.

Goals:

- keep metadata traces bounded by default;
- do not replay historical verbose tool output unnecessarily;
- do not fabricate assistant content as transport keepalive;
- preserve immediate tool semantics exactly even when history is compacted;
- full traces remain opt-in/private with retention and byte limits.

### P5 final release / operator diagnostics

Add bounded runtime identity evidence:

```text
UWA process start identity
git/build identity
listener PID/cwd
browser connected state
Codex compatibility/capability summary
current affinity binding counts/generation summary
```

No cookies, prompt bodies, command text, private paths beyond required local ownership checks, or full wire payloads should enter public logs/checkpoints.

## What we should explicitly NOT copy

### Do not replace Codex with a Runner

WebCodex needs a Runner because its online MCP client otherwise has no local executor. V2 already has one: Codex.

Adding another executor would create two competing owners for:

- filesystem policy;
- shell/process lifecycle;
- sandbox/approval;
- Git operations;
- project/worktree identity;
- long-running processes.

That would increase risk without advancing the target product.

### Do not build a second Job system

Stage D already proves Codex's long-process / `write_stdin` chain. The correct V2 work is preserving/recovering the Responses continuation around Codex execution, not adopting local child processes into UWA.

### Do not pivot P1.2 from context compaction to durable tasks

Durable task execution and LLM context compaction are different layers. WebCodex helps with the former; current P1.2 exists to prove the latter.

### Do not make public tunneling part of the V2 core

WebCodex requires public MCP reachability for hosted clients. UWA V2 currently runs locally between Codex and the controlled browser. Public HTTPS/Cloudflare/OpenAI MCP tunnels are not needed for the primary architecture and would expand the attack surface.

## Recommended V2 identity contract

Before P1.3 is implemented, document/test the following identity hierarchy:

```text
Codex thread
    durable user/task continuity selected by Codex

Responses response_id
    serialized protocol-history snapshot

Responses call_id
    one exact client tool call/result correlation

ChatGPT web conversation
    disposable transport affinity optimization

UWA process generation
    one runtime instance; process-local affinity dies with it

controlled browser/tab generation
    current browser execution binding only

Codex local process/job
    executor-owned state outside UWA authority
```

No arrow in this hierarchy grants authority to infer another identity. Recovery must use explicit mappings or persisted history, never heuristic identity collapse.

## Revised roadmap decision

The review changes **test depth**, not the product architecture or immediate order.

```text
CURRENT  migrate ~/.uwa/config_switch.py into Git
P1.2     native Codex large-context / compact / recovery        unchanged
P1.3     affinity/restart + identity fencing + uncertain effect expanded
Desktop  D1-D5 actual UI acceptance                            unchanged
P1.4     real-project long-task pilot                           unchanged
P2       serialization + queue planes + stale-result fencing   expanded
P3       MCP/schema/capability/fan-out fidelity                expanded
P4       bounded transcript/trace behavior                      strengthened
P5       runtime build identity + compatibility diagnostics     strengthened
```

This keeps the mainline moving while using WebCodex to avoid known reliability mistakes later.

## Attribution / copying policy

WebCodex is Apache-2.0 licensed. This review studies its public architecture and reliability contracts. No source code has been copied into V2 as part of this review.

If a later implementation directly adapts WebCodex code, the source path, upstream commit, Apache-2.0 attribution and local destination must be documented before merge.
