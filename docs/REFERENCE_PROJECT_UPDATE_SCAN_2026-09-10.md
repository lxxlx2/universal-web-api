# Reference-project update scan — 2026-09-10

## Scope

This scan covers the public projects already listed in `README.md` / `README.codex.en.md` as design or reliability references for the Codex Web Bridge V2 work. The primary activity window is 2026-09-05 through 2026-09-10. Recent OpenAI Codex releases/issues were also checked because changes there can alter the client/Responses contract that this bridge must satisfy.

No source code from the projects below was copied into this repository during this scan. The findings are design/reliability observations only unless a concrete UWA release blocker is explicitly identified below.

## Activity summary

```text
FlameFront-end/chatgpt-gateway         no commits observed in scan window
lininn/codex-proxy                     no commits observed in scan window
mehdic/codex-proxy                     no commits observed in scan window
openai/codex responses-api-proxy path  no commits observed in scan window
yyjeqhc/webcodex                       active; v0.4.0 + Sep 10 hardening commits
Waishnav/devspace                      active; recent agent/multi-agent documentation work
XiaoDuoYa/codex-with-chatgpt           active; recent Windows process polish; v0.1.2 nearby
alexanderradahl/mac-developer-bridge   no commits observed in scan window
```

## WebCodex findings

WebCodex v0.4.0, published on 2026-09-07, emphasizes durable workflow sessions, validation evidence, checkpoints/recovery, explicit Agent/Conversation/TaskAttempt identity boundaries, structured tool runtime semantics, exact-edit safety fences and closeout based on current validation evidence.

Sep 10 commits also tightened several file/runtime safety edges, including create-only race semantics, canonical-path validation before structured file edits/reads, sensitive-path checks and authorization preservation during cancellation.

Most of those file-edit/runtime details belong to a system that directly owns its execution tools. UWA Codex Web Bridge deliberately leaves filesystem edits and shell execution under the official Codex client's sandbox/approval boundary, so these are not reasons to expand the pre-main bridge surface.

Useful post-main ideas:

```text
durable attempt/checkpoint model for longer autonomous workflows
structured current-validation closeout records
explicit monotonic observation/checkpoint semantics
canonical-path/create-only safety if the standalone project later owns file tools
tool-definition driven admission/schema validation
```

## Codex with ChatGPT findings

The nearby v0.1.2 release focuses on structured MCP output schemas, persisted-record validation/sanitization, fail-closed tunnel startup health verification, avoiding duplicate bridge processes after an inconclusive probe, and quieter Windows background processes.

The bridge-health/process lessons are already represented by UWA's versioned lifecycle manager: owned-listener checks, health verification, verified stop/restart and fail-closed startup. Structured MCP output is valuable for a later connector/tool surface but is not required for the current Responses bridge release.

## DevSpace findings

Recent DevSpace activity in the scan window is primarily agent/multi-agent guidance, including XML/tool guidance and multi-agent wait semantics. That can inform later orchestration/documentation work but does not change the current Codex Responses compatibility contract.

## OpenAI Codex compatibility findings

Stable Codex 0.153.4 remains the release target used by the decisive current live acceptance. A newer 0.154 alpha exists, but moving the release gate to a prerelease client now would broaden the matrix without evidence that the stable target is invalid.

Recent public Codex reports remain especially relevant around compaction:

```text
remote compaction V2 must return exactly one compaction output item
compaction can replay an already-completed user instruction as newly actionable context
compaction can revive an obsolete earlier goal before the current goal resumes
some post-compaction threads stop or enter repeated compaction/context-limit loops
SSE response.failed handling can depend on clean stream termination
```

UWA already had decisive live proof that native remote V2 emits/accepts exactly one `type=compaction` output item and can recover the same thread afterward. Existing regression coverage keeps that contract explicit.

## Release-impacting finding found in UWA

This scan identified one separate UWA lifecycle hole that is release-critical.

`app/services/codex_remote_compaction_v2.py::_stream_remote_compaction_v2()` owns its own `_run_chat_completion_final()` asyncio backing task. Before this scan, that task was cancelled/awaited when the HTTP disconnect probe returned true, but the async generator had no unconditional cleanup for caller cancellation or explicit `aclose()` while the worker was still pending.

That is the same orphan-task class M4 closed for the ordinary streamed Responses attempt, on a different native remote-compaction code path. It must be fixed before M5 so the final regression gate tests one consistent lifecycle contract.

Release-blocking correction committed during this scan:

```text
aacfcef6d159abde226c192619cd80fa5d256d5b
Harden remote compaction cancellation and active-goal summary

e6f7578f67d2759b13992a259dff6c9bf9527632
Cover remote compaction cancellation cleanup
```

The production correction now:

```text
wraps the remote-compaction worker lifecycle in try/finally
cancels + awaits any still-pending backing task on generator unwind
preserves caller cancellation
preserves the existing HTTP-disconnect cleanup
leaves the normal completed worker untouched
```

Regression coverage verifies consumer cancellation and explicit `aclose()` cleanup. Existing remote-compaction V2 tests continue to cover normal completion and the exactly-one-compaction output contract.

The compaction summary prompt also now explicitly distinguishes completed historical requests from the current active goal and forbids presenting a completed old user request as a current actionable instruction. This is a narrow compatibility/safety mitigation for the recent stale-instruction replay reports and does not change normal tool routing or expand the release scope.

Security hardening CI for the final scan correction completed successfully.

## Deferred after main

The following ideas are useful but do not justify delaying the current release:

```text
structured MCP/connector output schemas
richer durable AgentTask/TaskAttempt/checkpoint orchestration
general multi-agent wait/orchestration UX
optional secure-tunnel/Desktop packaging work
Windows console/background-process polish beyond current supported release target
image-heavy history/token-volume optimization
canonical file/create-only fencing if a future standalone runtime owns file tools directly
```

These should be revisited after the verified V2 branch reaches `main`, preferably during the standalone S1 dependency/runtime audit so they are evaluated against the smaller intended architecture.

## Decision

The reference scan found one pre-main correctness item and it has been patched with regression coverage. Everything else remains post-main research so M5/M6/M7 release progress stays focused.
