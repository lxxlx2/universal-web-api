# UWA Codex Web Bridge V2

面向 Codex Desktop / Codex CLI 的本地 ChatGPT Web 推理桥。

目标是保留官方 Codex 的本地工作区、Shell、文件修改、测试、Git、sandbox 与 approval 能力，同时把模型推理通过本机 UWA 转发到已登录的 ChatGPT Web。网页模型负责分析和选择客户端工具，真正的本地操作仍由 Codex 客户端执行。

当前开发分支：`codex-web-bridge-v2`

长期状态与详细进度：

- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`

## 当前状态

```text
Stage A-F protocol / CLI acceptance                 PASS
aggregate A-F checker                               PASS
真实 exec_command / cwd / function_call loop        PASS
same-thread / restart continuity                    PASS
P1.1 legacy Responses compact direct live           PASS
P1.2 native auto-compact + remote V2 compaction     PASS / LIVE
P1.2 same-thread post-remote recovery               PASS / CLOSED
P1.3 minimal continuity blockers                    PASS / CLOSED
ChatGPT idle-composer send repair                   PASS / LIVE / CLOSED
Hybrid H0-H5                                        PASS / LIVE / CLOSED
M3a Hybrid Routing Safety                           PASS / LIVE / CLOSED
Desktop D1-D5                                       PASS / LIVE / CLOSED
M3b Desktop UI                                      PASS / LIVE / CLOSED
M4 real-project long-task pilot                     PASS / LIVE / CLOSED
remote-compaction cancellation follow-up            PASS / CI
M5 final regression                                 CURRENT
M6 CI / safety / docs / provenance                  pending
M7 merge verified V2 to main                        pending
```

M3a 已完成完整 official → UWA 合成 handoff 实机验收。最终状态证明 official source effect 和 UWA continuation effect 都恰好发生一次，真实 `exec_command` client tool round trip 成功，agent route 为 `uwa / chatgpt / high`，metadata helper 不计入 agent traffic，private transition ledger 通过，request-manager 最终归零。

详细记录：`docs/CODEX_HYBRID_M3A_LIVE_PASS_2026-09-10.md`。

M4 已在本仓库真实项目上完成长任务与 cancellation/orphan hardening。外层 streamed Responses 被取消或提前关闭时，`_run_chat_completion_final` backing task 会被 cancel + await，同时保留 caller cancellation 与正常完成语义。三项 focused regression、真实 Codex tool activity、`uwa / chatgpt / high` 路由和最终 request-manager 清理均已通过。

M4 记录：`docs/CODEX_M4_REAL_PROJECT_LONG_TASK_LIVE_PASS_2026-09-10.md`。

2026-09-10 对参考项目和近期 OpenAI Codex 兼容性变化的复核又发现一个同类但独立的 release blocker：native remote-compaction V2 路径也拥有自己的 backing task，原实现缺少 async-generator cancellation / `aclose()` 的 unconditional cleanup。该路径已经补上 `try/finally` cancel + await，并增加 consumer cancellation 与 `aclose()` regression；同时 compaction summary 明确区分“已完成历史请求”和“当前 active goal”，降低旧指令在 compaction 后重新变成 actionable 的风险。Security hardening CI 已通过。

参考项目复核：`docs/REFERENCE_PROJECT_UPDATE_SCAN_2026-09-10.md`。

当前进入 M5 final regression，使用一次命令完成 Stage A-F aggregate、全部 `test_codex_*.py` regression、当前代码 UWA restart，以及同一 Codex thread 跨真实 UWA restart 的 UWA/chatgpt/high continuity + real `exec_command` smoke，不使用 official provider。

M5 gate：`docs/CODEX_M5_FINAL_REGRESSION_GATE_2026-09-10.md`。

## 快速开始

安装或更新本地 helper：

```bash
cd ~/universal-web-api
git switch codex-web-bridge-v2
git pull --ff-only
python3 tools/install_codex_uwa_commands.py
```

进入 UWA 模式：

```bash
codex-uwa
```

切回官方 Codex provider：

```bash
codex-official
```

直接使用 provider switch helper：

```bash
python3 tools/codex_provider_switch.py uwa
python3 tools/codex_provider_switch.py official
```

基础检查：

```bash
curl -sS http://127.0.0.1:8199/health
python3 tools/codex_route_audit.py status
curl -sS http://127.0.0.1:8199/v1/codex/web-affinity
```

## official 与 UWA

```text
official
→ Codex 使用正常 signed-in account provider
→ 使用 Codex / Work 对应官方额度
→ provider/model/effort 由官方账号和客户端能力决定

UWA
→ model_provider = uwa
→ Codex 请求发送到本机 127.0.0.1:8199
→ UWA 使用当前登录 ChatGPT Web 做推理
→ 本地文件、Shell、测试、Git 仍由 Codex 客户端执行
```

provider switch 不修改登录凭据。已有 Desktop thread 可能保留旧 provider/model state，因此 config 或 UI label 不能单独作为真实执行路由证明。长任务应使用 fresh route marker/probe 和 authoritative session + wire metadata。

当前 UWA 默认：

```text
provider = uwa
model = chatgpt
reasoning effort = high
```

Medium 与 High 都需要由真实 Responses request 和 ChatGPT Web 页面状态验证。Low/Light 当前 UWA 路径不支持时 fail closed，不做静默降级。

## 架构

```text
Codex Desktop / CLI
        ↓
OpenAI Responses request
        ↓
UWA Codex Responses bridge
        ↓
ChatGPT Web / selected web model
        ↓
Responses function_call
        ↓
Codex client 在本机执行
        ↓
function_call_output
        ↓
同一 Responses / ChatGPT conversation continuation
        ↓
最终 response.completed
```

浏览器页面自身没有本机文件系统权限。真正的本地执行权限边界始终由 Codex client 的 sandbox 和 approval 决定。UWA 不替 Codex 绕过本地权限控制。

## Web Session Affinity 与 continuity

V2 使用 `previous_response_id`、call-id bridge 和 ChatGPT conversation affinity 尽量保持同一网页会话：

```text
首次 turn
→ response_id 绑定 ChatGPT conversation

client tool result
→ previous_response_id 或 call_id 找回 binding
→ 只发送新增 delta
→ continuation 留在同一 conversation
```

如果 mapping 丢失、UWA 重启、TTL 到期或页面不可恢复，则回退到 reconstructed history / persistent continuation，优先保证正确性。

项目连续性包含：

```text
Codex Desktop / CLI thread history
UWA private Responses persistence
process-local ChatGPT affinity
Git tracked project checkpoint
```

## Metadata helper 隔离

当前 Codex 会产生隐藏 thread-title 等 structured metadata request，并可能把真实用户任务作为数据嵌入其中。V2 在进入 required-tool、ChatGPT Web coding lane、affinity 和 agent-route accounting 前识别这类 request。

已识别 metadata helper：

```text
本地 deterministic structured response
不调用 exec_command
不进入 ChatGPT Web coding lane
trace request_kind = metadata_helper
route audit 不计入 agent traffic
```

真实编码请求记录为 `request_kind=agent_turn`。

## Required Tool Contract

当用户明确要求真实客户端工具，例如：

```text
必须使用 exec_command 执行 ...
You must use the local exec_command tool ...
```

V2 必须产生真正的 Responses `function_call`。纯文本模拟命令输出、声称工具不可用或只返回猜测结果都不算通过。

如果首次网页结果漏掉显式 required tool，V2 允许有限的 bounded repair。真实工具完成并返回匹配 `function_call_output` 后，不会因为重建历史仍包含原始要求而重复执行同一 effect。

## ChatGPT composer send repair

实机曾发现 ChatGPT 已处于 idle 且真实 `data-testid="send-button"` 可发送，但通用页面级 stop/streaming selector 误判成旧生成状态，导致 prompt 长时间停留在 composer。

当前实现优先验证 ChatGPT active composer 的真实 ready send button。修复后的 direct High live 已证明：

```text
prompt submitted                 YES
model output returned            YES
response.completed               YES
request-manager after            0
browser tab after                idle
```

## Context Compaction

支持两条 compact 路径：

```text
legacy POST /v1/responses/compact
native Codex remote V2 compaction_trigger through /v1/responses
```

Codex 0.153.4 native remote V2 已通过真实 macOS live，随后 same-thread recovery 也已关闭。UWA 的 opaque compact envelope 仅作为本地兼容状态，不宣称是 OpenAI encryption。

native remote-compaction stream 与普通 V2 stream 现在都遵循相同的 backing-task lifecycle：外层 generator unwind 时，仍 pending 的 Web worker 必须 cancel + await，避免 orphan browser/request work。

## Route audit 与 Hybrid Routing Safety

M3a H0-H5 已全部完成：

```text
H0 metadata-only route audit                  PASS
H1 exact provider/model/effort guard          PASS
H2 fresh Desktop route probe                  PASS / LIVE
H3 official -> UWA stateful handoff           PASS / LIVE
H4 private metadata-only transition ledger    PASS
H5 aggregate synthetic hybrid acceptance      PASS
```

Hybrid 第一版采用显式 handoff。未知 official quota 不猜测，也不自动静默切换。跨 provider continuation 以当前工作区/Git diff/测试状态等 durable local state 为主，新的 UWA thread 先检查已有 effect，再继续执行。

private hybrid ledger 只保存 route metadata 与 hash identity，不保存 prompt、command body、tool output 或 raw thread id。

## Wire Observability

默认 metadata trace：

```text
~/.uwa/debug/codex-wire
```

它用于证明真实 function call、response status、model/effort 等协议事实。默认 metadata capture 不保存 prompt、源码、命令正文或 tool output。

`full` capture 只能用于显式本地调试，可能含私有数据，严禁提交到 public repository。

## 当前 release path

```text
M1 P1.2 post-remote recovery                  PASS / CLOSED
M2 P1.3 minimal continuity                    PASS / CLOSED
M3a Hybrid Routing Safety H0-H5               PASS / LIVE / CLOSED
M3b Desktop D1-D5                             PASS / LIVE / CLOSED
M4 real-project long-task pilot               PASS / LIVE / CLOSED
M5 final A-F + compaction + restart regression CURRENT
M6 CI + public-repo safety + docs/provenance/license
M7 topology inspection + merge to main
```

M5 one-shot runner：

```text
tools/codex_m5_final_regression.py
```

M5 通过后进入最终 release-safety/docs/provenance 与 topology/merge 阶段，不再扩大首个稳定 `main` 的功能范围。

## Post-main standalone plan

verified V2 合并到 `main` 后：

```text
S1 dependency/import/runtime audit + core manifest
S2 create standalone attributed repository
S3 full CI + CLI/Desktop/live parity acceptance
S4 first standalone research release
```

独立仓库只移除经依赖证明不需要的通用 UWA 表面积。实际需要的 upstream runtime、AGPL-3.0、copyright/license notice 与明确 attribution 必须保留。

参考项目近期可借鉴但不影响当前发布的内容，例如 structured MCP output、durable AgentTask/TaskAttempt/checkpoint、multi-agent wait、可选 tunnel/Desktop packaging、image-heavy context 优化，会在 `main` 验证完成后结合 S1 dependency/runtime audit 再评估。

## 安全默认值

```text
API bind           127.0.0.1
CORS               disabled
Debug              disabled
Unsafe Python      disabled
Auto update        disabled
Remote access      disabled
DevTools           local only
```

public repository 禁止提交：

- `.env`、API Key、Token、密码
- Cookie、Session、Local Storage
- browser profile
- private UWA/Codex logs
- private prompt、tool body、tool output
- raw thread/process/browser identifiers
- `~/.uwa/codex_responses.sqlite3`
- `~/.uwa/debug/codex-wire`
- private hybrid handoff content
- Codex memory workspace 内容

## Attribution

当前仓库是 `lumingya/universal-web-api` 的 fork，并实际复用其浏览器/API/runtime 基础。这些部分继续受 upstream AGPL-3.0 与相应 copyright/license 义务约束。

V2 也研究了多个公开 coding bridge / Responses compatibility 项目的设计，包括 `FlameFront-end/chatgpt-gateway`、`lininn/codex-proxy`、`mehdic/codex-proxy`、OpenAI `codex-responses-api-proxy`、`yyjeqhc/webcodex`、`Waishnav/devspace`、`XiaoDuoYa/codex-with-chatgpt` 和 `alexanderradahl/mac-developer-bridge`。除实际 upstream 基础外，这些主要作为设计和可靠性研究来源；若直接复用具体代码，应在对应文件和 attribution 文档中单独标明。

详细来源与许可证：`docs/REFERENCES_AND_ATTRIBUTION.md`。

## 非官方声明

本项目用于个人学习、实验、协议兼容研究与工程验证，不是 OpenAI、ChatGPT、Codex 或其他参考项目的官方产品，也不代表任何合作、授权或背书。

本项目不会改变第三方服务本身的账号、订阅、额度或模型开放范围。使用者需要自行遵守所使用软件、网站和服务的适用条款、政策与法律要求。

---

## English project documentation

A dedicated English overview for the Codex Web Bridge V2 work is available at [`README.codex.en.md`](./README.codex.en.md).

The Chinese README above is preserved as-is. The repository's existing [`README.en.md`](./README.en.md) continues to describe the broader Universal Web API project, while `README.codex.en.md` focuses on the Codex-specific V2 architecture, routing, continuity, safety model, validation status and release path.
