# UWA Codex Web Bridge V2

面向 Codex Desktop / Codex CLI 的本地 ChatGPT Web 推理桥。

当前开发分支：`codex-web-bridge-v2`。

> Canonical: `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
>
> Progress: `docs/CODEX_WEB_BRIDGE_PROGRESS.md`

## 项目目标

保留官方 Codex Desktop / CLI 的本地 workspace、Shell、文件修改、测试、Git、sandbox 与 approval，同时把推理经本机 UWA 转发到已登录的 ChatGPT Web。

## 当前状态

```text
Stage A-F protocol/CLI                         PASS
A-F aggregate checker                          PASS
P1.1 legacy compact direct live                PASS
versioned lifecycle/provider switch            PASS
P1.2 stream/usage + TokenCount                 PASS
P1.2 native auto-compact trigger/local         PASS
P1.2 remote-capability shim implementation/CI  PASS (#351)
P1.2 remote V2 unary item/envelope repair      CURRENT
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

Remote capability 的 exact Codex 0.153.4 审计也已完成：最窄方案只把 managed UWA provider display name 设为 `Azure`，provider id 仍是 `uwa`，base URL 仍是本机 `127.0.0.1:8199/v1`，`wire_api=responses`，`requires_openai_auth=false`。对应 fail-closed helper 和测试已通过 Security hardening #351；对齐后的 #355 也 PASS。

实机启用前又确认了一个更窄的协议 blocker。纠正后的 exact-release 事实是：`/responses/compact` **仍是 unary HTTP**，不需要 SSE。当前 P1.1 transport 已正确；差异只在返回 item：

```text
当前 UWA P1.1:
output=[assistant message]

Codex 0.153.4 remote V2:
output=[{
  type: compaction,
  encrypted_content: <opaque payload>
}]
```

Codex V2 collector 要求 Compaction item 数量恰好为 1，否则直接失败。因此现在先实现 dual-path unary contract：无 `compaction_trigger` 继续保持 P1.1；有 trigger 时生成同样的 bounded web summary，但包装成 UWA-owned opaque compaction envelope。后续普通 Responses 输入还必须能把 UWA 自己的 envelope 解码回 model-visible compact context，并对 foreign/corrupt envelope fail closed。

字段名虽然叫 `encrypted_content`，UWA 不会把自己的本地 envelope 宣称为 OpenAI encryption。

详细记录：

- `docs/CODEX_P1_AUTO_COMPACT_TRIGGER_LIVE_PASS_2026-09-08.md`
- `docs/CODEX_P1_REMOTE_COMPACTION_CAPABILITY_AUDIT_2026-09-08.md`
- `docs/CODEX_P1_REMOTE_V2_PROTOCOL_GAP_2026-09-08.md`

## 日常命令

进入 UWA 模式：

```bash
cd ~/universal-web-api
git switch codex-web-bridge-v2
git pull
python3 tools/install_codex_uwa_commands.py
codex-uwa
```

切回官方账号模式：

```bash
cd ~/universal-web-api
python3 tools/codex_provider_switch.py official
```

## 后续路线

```text
P1.2 V2 item/envelope repair → CI → native remote compact live → same-thread recovery
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
