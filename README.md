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
P1.2 remote V2 ordinary Responses repair       CURRENT
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

实机启用前继续追 exact release 后，remote V2 的真实路由已经钉死：

```text
legacy remote compact
→ unary /v1/responses/compact

Codex 0.153.4 remote V2
→ input 末尾追加 compaction_trigger
→ ModelClientSession.stream()
→ 普通 Responses HTTP transport
→ /v1/responses
```

我们的 provider 明确 `supports_websockets=false`，所以 V2 会走普通 HTTP Responses streaming。Codex V2 collector 要求该 stream 里恰好一个：

```text
type = compaction
encrypted_content = <opaque payload>
```

当前普通 UWA Responses 路由尚未识别 `compaction_trigger`，因此 Azure capability shim 暂时不能实机启用。P1.1 的 `/responses/compact` PASS 仍然有效，但它属于另一条 legacy compact 路径，不能代替 V2。

现在修复普通 `/v1/responses` V2 compact：验证并剥离 trigger、通过 ChatGPT Web 生成 bounded no-tools summary、包装为 UWA-owned bounded/integrity-checked opaque envelope、以正常 Responses SSE 发出恰好一个 `type=compaction` item；后续普通 Responses 输入再把有效 UWA envelope 解码回 model-visible compact context。foreign/corrupt/oversized envelope 必须 fail closed。

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
P1.2 V2 Responses repair → CI → native remote compact live → same-thread recovery
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
