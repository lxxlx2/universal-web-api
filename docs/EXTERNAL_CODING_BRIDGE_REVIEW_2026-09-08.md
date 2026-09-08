# Adjacent ChatGPT coding bridge review — 2026-09-08

## Scope

This review compares the active UWA Codex Web Bridge V2 architecture with four adjacent public projects mentioned during the P1.2 hardening work.

Reviewed snapshots:

- `yyjeqhc/webcodex` — previously reviewed at `5a4da8fff7a7dc52bd963e8dc22ef530160f28`; refreshed through current head `79e61cc85008bf35e4eea02abd137531afdba968`.
- `Waishnav/devspace` — reviewed at `d74ece04adc2a80ebed07c2798407b3be668b0f1`.
- `XiaoDuoYa/codex-with-chatgpt` — reviewed at `a9f91cd98df1bc82686f57d5bc2b2993394c93be`.
- `alexanderradahl/mac-developer-bridge` — reviewed at `fea70d1a3c5524164f2159f6063ba685fef91324`.

The purpose is design extraction, not source copying and not an architecture pivot.

## Non-negotiable UWA architecture

The current project keeps this authority split:

```text
ChatGPT Web
    reasoning / tool choice
        ↓
UWA
    Responses/browser compatibility, continuity, tracing
        ↓
Official Codex Desktop / CLI
    filesystem, shell, Git, edits, tests, processes, sandbox, approval
```

UWA will not add a second local coding Runner merely because adjacent projects expose their own MCP executor. Official Codex already owns the local execution boundary we want.

The P1.2 native remote-compaction macOS live gate remains the current gate. This review must not delay or replace it.

## 1. WebCodex refresh

The original WebCodex review already contributed the strongest reliability ideas in the roadmap: stable logical identity versus process generation, uncertain-effect reconciliation, concurrency-plane separation, bounded observation state, fail-closed capability negotiation and non-authoritative correlation IDs.

Two newer upstream changes are directly relevant.

### Typed invocation metadata must not hide inside business tool arguments

Recent WebCodex work separates protocol/session invocation metadata from concrete business tool arguments instead of recovering hidden control fields from the JSON argument object.

Adopt for UWA:

- model-authored client tool arguments remain the business payload only;
- UWA observation/session/generation/correlation metadata stays in bridge-owned side state or typed protocol state;
- hidden UWA metadata must never acquire execution authority merely because it appears inside tool arguments;
- future normalization should explicitly strip/reject bridge-private fields before they can reach Codex.

Roadmap placement: P1.3/P2.

### Centralized governance for specialized gateways

WebCodex now centralizes shared governance for heterogeneous gateways while leaving each gateway responsible for its own action vocabulary and effect semantics.

Adopt for UWA:

- future provider/browser/specialized adapters should enter through one explicit policy boundary rather than accumulating route-specific permission/retry branches;
- shared governance decides compatibility, generation/fencing and retry eligibility once;
- adapter-specific code owns protocol translation and effect classification;
- one logical invocation must dispatch exactly once.

Roadmap placement: P2/P3.

## 2. DevSpace

DevSpace turns ChatGPT into the coding agent through a self-hosted MCP server. That executor architecture is intentionally different from ours, but several operational controls are valuable.

### Useful patterns

1. **Narrow workspace roots**
   - explicit allowed roots are easier to reason about than broad home/root access;
   - worktree isolation is treated as a workflow boundary rather than falsely advertised as a security boundary.

2. **`doctor` / preflight UX**
   - runtime prerequisites and configuration are checked before a real session begins;
   - this fits our P5 runtime/build identity and provider/browser preflight work.

3. **Protocol compatibility at one endpoint**
   - DevSpace supports newer and older MCP client shapes without exposing a manual protocol-mode switch;
   - the general lesson is to negotiate/normalize at the protocol edge and keep one canonical internal representation.

4. **Bounded, metadata-focused logging**
   - command body logging is opt-in;
   - transfer logs use hashes/counts/status instead of opaque source values or content.

5. **One-shot artifact transfer**
   - native file download is bound to an already-open workspace, uses relative destinations, refuses overwrite/traversal/symlink escape and does not create a reusable public artifact service.

### What UWA should adopt

- explicit preflight/doctor command covering provider contract, listener identity, browser attachment, context catalog, local persistence permissions and public-repo safety;
- continue treating cwd/workspace authority as explicit and bounded, never inferred from browser state;
- if artifact ingress is added later, prefer one-shot workspace-scoped transfer with no reusable public object capability;
- normalize future protocol-version differences at the edge.

### What UWA should not adopt

- no public MCP tunnel in the core Codex-to-UWA path;
- no duplicate shell/filesystem executor inside UWA;
- no broad filesystem root registry replacing Codex's own workspace/sandbox authority.

Roadmap placement: P3/P5.

## 3. codex-with-chatgpt

This project deliberately keeps ChatGPT as planning/review and Codex as executor, so its authority split is the closest conceptual neighbor to UWA even though its transport is read-only MCP plus browser control.

### Useful patterns

1. **Control plane versus data plane**
   - control messages carry bounded state, never diffs/logs/file bodies;
   - actual evidence is fetched separately through structured tools.

2. **Independent review of execution evidence**
   - after Codex says an iteration is finished, ChatGPT independently inspects git diff/test/execution records instead of trusting the success claim.

3. **Workspace is the authorization boundary**
   - tokens and connector identity are bound to one workspace;
   - path canonicalization, traversal checks and sensitive-file policy are centralized.

4. **Execution-output sanitization**
   - selected command output is locally sanitized, capped and can be withheld entirely when unsafe;
   - the control channel only receives metadata.

5. **Finite state and checkpoint/handoff discipline**
   - explicit PLAN/EXECUTED/REVIEW/DONE-style state prevents free-form orchestration drift;
   - local checkpoint state is distinguished from model-visible protocol state;
   - handoff is a bounded brief rather than a transcript dump;
   - current code/evidence outranks summaries and memory when facts conflict.

### What UWA should adopt

- strengthen the real-project pilot so success is based on independently observed diff/test/tool evidence, not final prose;
- keep control/observation metadata separate from private content;
- add a bounded evidence/trust-order rule to P4: current executor/tool evidence > current client-supplied history > compact/handoff summaries > older cached state;
- preserve finite retry/iteration budgets and explicit terminal failure classifications;
- keep sensitive/private execution bodies out of default traces.

### What UWA should not adopt

- no second MCP data plane is required for normal Codex execution because Codex already has the local workspace and tools;
- no ChatGPT Project memory requirement in the core bridge;
- no public tunnel/OAuth connector dependency for the local inference path.

Roadmap placement: P4 plus the real-project pilot gate.

## 4. Mac Developer Bridge

Mac Developer Bridge gives ChatGPT broad direct authority over a Mac. Its default authority model is intentionally much wider than UWA's, so we should not copy its execution architecture. Its process/browser lifecycle engineering is still useful.

### Useful patterns

1. **Real PTY and process-group lifecycle**
   - long-running jobs have explicit start/status/log/kill semantics;
   - kill operates on the process group, not merely one PID.

2. **Audit trail and kill switch**
   - runtime has a local audit tail and explicit disable path;
   - a fail-closed unlock latch is checked before tool execution.

3. **Read-only stored Codex history inspection**
   - stored threads can be inspected without creating another Codex model turn.

4. **Background browser workspace leases**
   - browser tabs are leased, reused and reclaimed;
   - active operations renew the lease;
   - stale/abandoned leases expire;
   - pool growth and focus policy are explicit rather than incidental.

5. **First-party ChatGPT runtime submission experiment**
   - the project experiments with invoking the page's mounted first-party composer action instead of UI typing/clicking, while leaving credential/proof construction to ChatGPT's own runtime.

### What UWA should adopt

- P2 browser-affinity hardening should explicitly model lease/generation/heartbeat/reclaim rather than only pathname affinity;
- stale browser generations must be fenced before a retry can reuse them;
- lifecycle commands should retain a verified kill/disable path and bounded metadata audit;
- P5 can research first-party page-runtime submission as an optional transport to reduce DOM brittleness, but only after the current browser path is stable and only with strict fallback/verification.

### What UWA should not adopt

- no unrestricted shell/filesystem authority in UWA;
- no direct replacement of Codex's PTY/background-process implementation;
- no automatic reading of private Codex rollout/session files as a continuity mechanism;
- no broad authenticated-browser control surface in the core bridge.

Roadmap placement: P2/P5.

## Consolidated adoption plan

```text
CURRENT
P1.2 native remote compaction macOS live
→ same-thread post-remote recovery

P1.3
→ stable logical identity vs process/browser generation
→ uncertain-effect reconciliation before retry
→ typed bridge metadata kept outside business tool arguments
→ private/hidden metadata never grants execution authority

P2
→ per-continuation serialization and concurrency-plane separation
→ browser lease/generation/heartbeat/reclaim fencing
→ one shared governance boundary for specialized adapters
→ exactly-once dispatch identity across queued/retried work

P3
→ MCP/schema/capability fidelity using WebCodex + DevSpace as references
→ protocol-edge version normalization
→ optional one-shot workspace-scoped artifact ingress design, if needed

P4 / real-project pilot
→ independent diff/test/tool evidence review
→ bounded execution evidence and sanitization
→ explicit evidence trust ordering
→ finite state/iteration/retry classification

P5
→ doctor/preflight and runtime/build identity
→ verified disable/kill path and bounded audit
→ optional research: first-party ChatGPT page-runtime submission transport
```

## Architecture decision

No architecture pivot is warranted.

The adjacent projects reinforce the current UWA direction: keep execution authority in official Codex, make protocol metadata non-authoritative, make effects observable, separate control state from content, fence stale runtime generations, independently verify outcomes, and provide strong preflight/disable diagnostics.

The current P1.2 live gate remains unchanged.