# UWA Codex Web Bridge V2

面向 Codex Desktop / Codex CLI 的本地 ChatGPT Web 推理桥。

当前开发分支：`codex-web-bridge-v2`。

> Canonical engineering state: `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
>
> Progress log: `docs/CODEX_WEB_BRIDGE_PROGRESS.md`

## 项目目标

保留官方 Codex Desktop / CLI 的本地工作区、Shell、文件修改、测试、Git、sandbox 与 approval 能力，同时把模型推理通过本机 UWA 转发到已登录的 ChatGPT Web。网页模型负责分析和选择客户端工具，真实本地操作仍由 Codex 客户端执行。

## 当前状态

```text
Stage A-F protocol/CLI                         PASS
A-F aggregate checker                          PASS
P1.1 legacy compact direct live                PASS
versioned lifecycle/provider switch            PASS
P1.2 stream/usage + TokenCount                 PASS
P1.2 native auto-compact trigger/local         PASS
P1.2 remote-capability shim implementation/CI  PASS (#351)
P1.2 remote V2 protocol repair                 CURRENT
Codex Desktop UI live gate                     REQUIRED BEFORE MAIN MERGE
```

Native small-step trigger 已真实 macOS PASS：

```text
57429 < 57600
58290 > 57600
ROLLOUT_COMPACT_MARKER_DELTA=1
REMOTE_COMPACT_ROUTE_DELTA=0
REMOTE_COMPACT_SUCCESS_DELTA=0
AUTO_COMPACT_MODE=LOCAL_FALLBACK
AUTO_COMPACT_TRIGGER_PROBE_PASS
```

Remote capability 也已完成 exact Codex 0.153.4 审计和 fail-closed implementation：只把 managed UWA provider 的 display name 设为 `Azure`，provider id 仍为 `uwa`，base URL 仍为本机 `127.0.0.1:8199/v1`，`wire_api=responses`，`requires_openai_auth=false`。Security hardening #351 PASS；最新对齐后的 #355 也 PASS。

但在真正启用 shim 前确认了新的协议 blocker：当前 P1.1 `/v1/responses/compact` 是 legacy unary assistant-message response；Codex 0.153.4 remote V2 则要求 SSE stream，并且必须恰好收到一个：

```text
type=compaction
encrypted_content=<opaque payload>
```

Codex exact-release collector 会在 compaction item 数量不是 1 时直接失败。因此现在先修 dual-path compact protocol，不让 macOS 跑一个已知会失败的实验。

当前 repair 要求：

```text
legacy unary compact
→ 保留现有 P1.1 assistant-message contract

streaming compaction_trigger
→ ChatGPT Web 生成 compact summary
→ UWA-owned opaque bounded envelope
→ response.output_item.done(type=compaction)
→ response.completed
```

随后普通 Codex Responses 转发必须能把 UWA-owned envelope 解码回 model-visible compact context；foreign/corrupt envelope fail closed。字段名虽然叫 `encrypted_content`，UWA 不会把本地 envelope 宣称为 OpenAI encryption。

详细记录：

- `docs/CODEX_P1_AUTO_COMPACT_TRIGGER_LIVE_PASS_2026-09-08.md`
- `docs/CODEX_P1_REMOTE_COMPACTION_CAPABILITY_AUDIT_2026-09-08.md`
- `docs/CODEX_P1_REMOTE_V2_PROTOCOL_GAP_2026-09-08.md`

## 快速进入 UWA 模式

首次安装：

```bash
cd ~/universal-web-api
git switch codex-web-bridge-v2
git pull
python3 tools/install_codex_uwa_commands.py
codex-uwa
```

日常：

```bash
codex-uwa
```

## 一键切回官方账号模式

```bash
cd ~/universal-web-api
python3 tools/codex_provider_switch.py official
```

官方模式不固定模型/reasoning，由账号和 UI 决定可用模型。

## 后续路线

```text
P1.2 remote V2 protocol repair → CI → native remote compact live → same-thread recovery
P1.3 lost-affinity / restart + identity fencing + uncertain-effect recovery
Desktop D1-D5 actual UI acceptance
P1.4 real-project long-task pilot
P2-P5 production hardening / final release gate
```

## 合并与安全

`codex-web-bridge-v2` 暂不合并到 `main`。P1 hardening、Desktop D1-D5、真实项目 pilot、最终回归/CI/docs/public-repo-safety 全绿后才进入最终合并。

不得提交 browser profile、cookie/local storage、credentials、private UWA/Codex logs、raw wire traces、Responses SQLite、真实 thread/process/browser identifier、Codex memory workspace、用户私有项目源码或 acceptance 捕获的私有 prompt/tool body。

## 项目说明

本项目是个人实验、协议兼容研究和工程验证项目，不是 OpenAI、ChatGPT、Codex、WebCodex 或其他参考项目的官方产品，也不代表这些项目或公司的认可、合作、授权或背书。
