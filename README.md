# UWA Codex Web Bridge V2

面向 Codex Desktop / Codex CLI 的本地 ChatGPT Web 推理桥。

当前开发分支：`codex-web-bridge-v2`。

> Canonical engineering state: `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
>
> Progress log: `docs/CODEX_WEB_BRIDGE_PROGRESS.md`

## 项目目标

保留官方 Codex Desktop / CLI 的本地工作区、Shell、文件修改、测试、Git、sandbox 与 approval 能力，同时把模型推理通过本机 UWA 转发到已登录的 ChatGPT Web。网页模型负责分析和选择客户端工具，真实本地操作仍由 Codex 客户端执行。

```text
Codex Desktop / CLI
        ↓
OpenAI Responses
        ↓
UWA V2 bridge
        ↓
ChatGPT Web
        ↓
structured function_call
        ↓
Codex local execution
        ↓
function_call_output
        ↓
continue task
```

## 当前实机状态

```text
Stage A-F protocol/CLI                    PASS
A-F aggregate checker                     PASS
Responses tool round trip                 PASS
P1.1 Responses compact direct live        PASS
versioned lifecycle/provider switch       PASS
P1.2 stream/usage compatibility           PASS
P1.2 second full large-context live       FAIL
P1.2 rollout TokenCount diagnosis         CURRENT
Codex Desktop UI live gate                REQUIRED BEFORE MAIN MERGE
```

P1.2 第一次完整实测暴露 SSE idle heartbeat 与 all-zero usage 两个兼容缺口。修复后 Security hardening CI #313 与真实 macOS non-zero usage smoke 均 PASS。

第二次完整实测中，同一 Codex thread 的 input usage 从 `21230` 连续增长到 `250919`，但 rounds 1-7 没有当前 run 的 `/v1/responses/compact` route/success marker，round 8 filler contract FAIL。

只读诊断确认 cached/live model catalog 都是 64K context、57,600 truncation limit，且没有顶层 context-window 或 auto-compact override，因此 stale cache 与配置覆盖已排除。

精确核对实际安装版本：Codex `0.153.4` 对应 `rust-v0.153.4` / commit `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`。该版本只把 OpenAI 或 Azure identity 的 configured provider 标记为 remote compaction V2；当前 UWA provider 因此是 `RemoteCompactionSupport::Unsupported`，但仍保留 local auto-compaction fallback。

同一版本源码还确认：resume/fork 会从 rollout 中最后一个 `EventMsg::TokenCount` 恢复 token usage；正常 `response.completed` 会记录 usage 并发送 `TokenCount`，普通 event 默认会持久化进 rollout。因此“每次 `codex exec resume` 都天然丢 usage”这一假设已被否定。

当前唯一下一步是只读检查本次真实 P1.2 rollout 中是否存在 `TokenCount`，以及其安全的 numeric token totals / model context window。确认前不重复完整 stress run，也不手工把 provider 改成 `OpenAI`/`Azure`。

## 当前 P1.2 证据文档

- `docs/CODEX_P1_LARGE_CONTEXT_ACCEPTANCE_2026-09-08.md`
- `docs/CODEX_P1_LARGE_CONTEXT_LIVE_FAILURE_2026-09-08.md`
- `docs/CODEX_P1_LARGE_CONTEXT_SECOND_LIVE_FAILURE_2026-09-08.md`
- `docs/CODEX_P1_STREAM_COMPAT_REPAIR_2026-09-08.md`
- `docs/CODEX_P1_STREAM_USAGE_LIVE_SMOKE_2026-09-08.md`
- `docs/CODEX_P1_MODEL_CACHE_RESUME_DIAG_2026-09-08.md`

## 连续性设计

1. Codex Desktop / CLI thread history。
2. UWA private Responses persistence：`~/.uwa/codex_responses.sqlite3`。
3. process-local ChatGPT web-session / call-id affinity。
4. Git tracked checkpoint 作为跨对话、跨协作者长期项目事实来源。

Codex thread、Responses `response_id`、tool `call_id`、ChatGPT Web conversation、UWA process、controlled tab 和 Codex local execution state 是不同 identity domain。P1.3 会继续验证 lost-affinity、generation fencing 与 uncertain-effect recovery。

## 快速进入 UWA 模式

首次安装仓库受控 wrapper：

```bash
cd ~/universal-web-api
git switch codex-web-bridge-v2
git pull
python3 tools/install_codex_uwa_commands.py
codex-uwa
```

安装后日常进入 UWA 模式：

```bash
codex-uwa
```

正常 UWA 启动链路不再依赖 `~/.uwa/config_switch.py`。

## 一键切回官方账号模式

```bash
cd ~/universal-web-api
python3 tools/codex_provider_switch.py official
```

官方账号模式不固定模型或 reasoning；切换后由账号/工作区与 Desktop UI 决定可用模型。

## WebCodex 参考

`yyjeqhc/webcodex` 已作为 Apache-2.0 设计参考审计。项目不采用其 Server + Runner 执行层；官方 Codex 继续拥有 filesystem/shell/Git/sandbox/approval。吸收重点是 request-loss/execution-loss 分离、uncertain-effect reconciliation、generation fencing、bounded diagnostics、MCP capability discipline 与并发 plane 分离。

详细审计：`docs/WEBCODEX_ARCHITECTURE_REVIEW_2026-09-07.md`。

## 后续路线

```text
P1.2 rollout TokenCount diagnosis → native compact/recovery
P1.3 lost-affinity / restart + identity fencing + uncertain-effect recovery
Desktop D1-D5 actual UI acceptance
P1.4 real-project long-task pilot
P2 per-continuation serialization / queue planes / stale-result hardening
P3 MCP/plugin namespace + capability fidelity + multi-agent/tool fan-out
P4 Responses SSE slimming + bounded trace/transcript hygiene
P5 runtime/build identity + compatibility preflight + final regression/release checklist
```

## 合并门槛

`codex-web-bridge-v2` 暂不合并到 `main`。需要 P1 hardening 无 blocker、Desktop D1-D5 PASS、真实项目长任务 pilot PASS、最终 CI/回归/docs/public-repo-safety 全绿，并在最终合并前检查 `main` / `security-hardening` / V2 ancestry。

## Public repository safety

不得提交 browser profile、cookie/local storage、credentials、private UWA/Codex logs、raw wire traces、Responses SQLite、真实 thread/process/browser identifier、Codex memory workspace、用户私有项目源码或 acceptance 捕获的私有 prompt/tool body。

## 项目说明

本项目是个人实验、协议兼容研究和工程验证项目，不是 OpenAI、ChatGPT、Codex、WebCodex 或其他参考项目的官方产品，也不代表这些项目或公司的认可、合作、授权或背书。
