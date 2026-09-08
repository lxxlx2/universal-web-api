# UWA Codex Web Bridge V2

面向 Codex Desktop / Codex CLI 的本地 ChatGPT Web 推理桥。

目标是保留官方 Codex 的本地工作区、Shell、文件修改、测试、Git、sandbox 与 approval 能力，同时把模型推理通过本机 UWA 转发到已登录的 ChatGPT Web。网页模型负责分析和选择客户端工具，真正的本地操作仍由 Codex 客户端执行。

当前开发分支：`codex-web-bridge-v2`

长期状态与详细进度：

- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`

README 只维护项目说明、使用方式、架构、安全边界和当前阶段摘要；细粒度 live acceptance、失败记录和修复 checkpoint 统一放在 `docs/`。

## 当前状态

当前已验证：

```text
Stage A-F protocol / CLI acceptance                 PASS
aggregate A-F checker                               PASS
真实 exec_command / cwd / function_call loop        PASS
同一 ChatGPT Web conversation tool continuation    PASS
长进程 + write_stdin                                PASS
same-thread / restart continuity                    PASS
P1.1 legacy Responses compact direct live           PASS
versioned UWA lifecycle/provider switch             PASS
P1.2 stream/usage + TokenCount                      PASS
P1.2 native auto-compact trigger/local fallback     PASS
P1.2 remote capability shim implementation/CI       PASS
P1.2 remote V2 ordinary Responses implementation/CI PASS
P1.2 UWA provider precondition live                 PASS
P1.2 native remote compact macOS live               PASS
P1.2 same-thread post-remote recovery               PASS / CLOSED
P1.3 minimal continuity blockers                    PASS / CLOSED
Hybrid H0 route audit                               PASS / CI
Hybrid H1 route/model/effort guard                  PASS / CI
Hybrid H2 fresh Desktop route probe                 PASS / LIVE
Hybrid H3-H5                                        CURRENT / mandatory
Codex Desktop D1                                    PASS / LIVE / CLOSED
Codex Desktop D2                                    READY / CURRENT
Codex Desktop D3-D5                                 pending / mandatory
```

Codex 0.153.4 的 native remote V2 compaction、同线程恢复和最小 continuity blockers 已完成。fresh Desktop probe 实机证明了 `uwa / chatgpt / high` 的新线程路由，包含健康的 UWA/browser 状态、marker 后真实 UWA request/response 和 exact route expectation PASS。随后 Desktop D1 也已实机通过：实际 Codex Desktop UI 完成多文件修改和测试，独立 checker 返回 `ACCEPTANCE_PASS`，metadata-only trace 证明真实 `exec_command` function call 与 completed Responses turn。当前 release-critical 主线进入 Desktop D2 same-thread continuation，并继续保留 H3-H5 作为 `main` 前的最小 Hybrid Routing Safety 工作。

详细记录：

- `docs/CODEX_P1_REMOTE_V2_LIVE_PASS_2026-09-08.md`
- `docs/CODEX_P1_REMOTE_V2_RECOVERY_CLOSED_2026-09-08.md`
- `docs/CODEX_P1_3_MINIMAL_CONTINUITY_CLOSED_2026-09-08.md`
- `docs/CODEX_HYBRID_ROUTING_SAFETY_2026-09-08.md`
- `docs/CODEX_HYBRID_H2_FRESH_ROUTE_PROBE_PASS_2026-09-08.md`
- `docs/CODEX_DESKTOP_D1_LIVE_PASS_2026-09-08.md`
- `docs/ACCELERATED_MAIN_MERGE_GATE_2026-09-08.md`

## 快速开始

安装/更新本地 helper：

```bash
cd ~/universal-web-api
git switch codex-web-bridge-v2
git pull
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

也可以直接使用 provider switch helper：

```bash
python3 tools/codex_provider_switch.py uwa
python3 tools/codex_provider_switch.py official
```

基础检查：

```bash
curl -sS http://127.0.0.1:8199/health
curl -sS http://127.0.0.1:8199/v1/codex/wire-trace
curl -sS http://127.0.0.1:8199/v1/codex/web-affinity
```

### official 与 UWA 模式的区别

Codex Desktop / CLI 中“登录了哪个账号”和“当前推理请求走哪个 provider”是两个不同层面。

```text
official 模式
→ Codex 使用正常的官方 provider / account backend
→ 使用 Codex / Work 对应的官方额度
→ 可使用当前官方账号和客户端提供的模型 / 能力

UWA 模式
→ model_provider = "uwa"
→ Codex 请求发到本机 127.0.0.1:8199
→ UWA 把推理转发给当前已登录的 ChatGPT Web
→ 不使用 Codex / Work 的官方推理额度
→ 可用模型 / 推理档取决于该 ChatGPT Web 账号和网页实际提供的能力
```

因此，UWA 模式不会让 Codex 同时获得官方 Codex 专属额度、官方专属模型或 ChatGPT Web 没有开放的模型/能力；需要这些能力时应切回 official 模式。反过来，仅仅在 Desktop 中保持官方账号登录，也不会让一个已经启动在 `model_provider="uwa"` 下的新 Codex CLI 请求自动绕过 UWA。

provider switch 不修改登录凭据。切回 official 模式时会移除 UWA 的顶层 provider/model/reasoning pin，让正常账号模式重新接管模型选择。

### UWA 推理强度：Medium 与 High 有实际区别

当前 bridge 不把 Codex Desktop 中“看起来选中了哪个强度”直接当成事实。真正有效的强度以 **送到 UWA 的 Responses `reasoning.effort` + ChatGPT Web 页面验证结果** 为准。

当前语义：

```text
High    支持；也是 versioned UWA provider 的默认值
Medium  支持；当真实 Responses request 携带 medium 时，UWA 会把网页切到 Medium / 中并验证
Low     当前不支持；bridge 会 fail closed，不会偷偷当成 High
```

因此 Medium 和 High 在 UWA 模式下不是同一个档位。Desktop 的滑块/菜单只有在后续 Desktop UI 验收中证明“UI 选择 → request effort → 网页 Medium/High”完整贯通后，才能视为真正生效。

详细语义：`docs/CODEX_REASONING_EFFORT_SEMANTICS_2026-09-08.md`。

## 架构

```text
Codex Desktop / CLI
        ↓
OpenAI Responses request
        ↓
UWA Codex Responses bridge
        ↓
previous_response_id / call_id → ChatGPT /c/... affinity
        ↓
ChatGPT Web / selected web model
        ↓
结构化客户端工具调用
        ↓
Codex 在本机执行
        ↓
function_call_output
        ↓
同一 ChatGPT conversation 增量继续
        ↓
直到最终答案
```

浏览器页面自身没有本机文件系统权限。本地文件、Shell、测试和 Git 能力来自 Codex 客户端，Codex 自己的 sandbox 和 approval 始终是本地执行权限边界。

UWA 不直接替 Codex 执行本地 shell 命令，它负责把 ChatGPT Web 的模型输出转换为 Codex 能消费的 Responses/tool protocol，并把客户端工具结果继续送回同一个模型会话。

## V2 Web Session Affinity

旧流程在每个外层 Responses turn 前都会准备 fresh composer，而通用 UWA workflow 默认也会执行 `new_chat_btn`。一个简单工具循环可能变成：

```text
用户任务
→ 新 ChatGPT 对话
→ function_call
→ Codex tool result
→ 再开新 ChatGPT 对话并重放历史
→ function_call
→ 再开新对话
```

V2 把网页会话连续性和 Responses 连续性绑定。正常路径使用 `previous_response_id`：

```text
首次 Codex turn
→ 创建 fresh ChatGPT conversation
→ response_id A 绑定到 /c/...

Codex 返回 function_call_output
→ previous_response_id=A
→ 恢复同一个 /c/...
→ 只发送新增 tool result
→ response_id B 继续绑定同一个 /c/...
```

实机还观察到 Codex 可能以重建历史形式回传工具结果，没有可直接使用的 UWA `previous_response_id`。因此增加 metadata-only call bridge：

```text
function_call call_id
→ 记录 call_id -> response_id
→ response_id 已绑定 /c/...

function_call_output call_id
→ 找回 response_id
→ 找回同一个 /c/...
→ 只发送 function_call_output delta
```

关键规则：

1. response / call affinity 只保存协议关联信息，不保存 prompt、命令正文或 tool output。
2. continuation 复用时不重放完整 Codex transcript，只把新增 Responses delta 发到已有网页会话。
3. 已经存在匹配 `function_call + function_call_output` 时，同一个 required-tool 不会再次被强制执行。
4. Codex 浏览器轮次会抑制通用 workflow 的 `new_chat` 决策，内部 repair round 也继续当前网页 conversation。
5. 映射丢失、TTL 到期、UWA 重启、页面不可恢复或模型/推理档不匹配时，优先保证正确性并回退到 reconstructed history / persistent continuation 路径。

本地只读状态接口：

```text
GET /v1/codex/web-affinity
```

它只返回启用状态、binding 数量、TTL、容量和 fallback 类型，不暴露 conversation pathname。

## Responses Continuity

项目有四层连续性：

1. Codex Desktop / CLI thread history。
2. UWA private Responses continuation：`~/.uwa/codex_responses.sqlite3`。
3. 进程内 ChatGPT web-session / call-id affinity。
4. Git tracked checkpoint，作为长期项目事实来源。

Stage E-F 已验证 same-thread 和 restart continuity。短期浏览器 affinity 丢失不应破坏项目工作区或 Git 状态，恢复策略以 Codex thread、client-supplied history、private Responses persistence 和 Git checkpoint 为准。

## V2 Wire Observability

默认 metadata trace 路径：

```text
~/.uwa/debug/codex-wire
```

它用于区分：

```text
网页模型只是输出了一段看似命令结果的文字
```

和：

```text
UWA 真的向 Codex 发出了 Responses function_call
```

metadata 默认记录：

- Responses event 顺序
- function call 名称
- argument keys
- argument 长度与短 hash
- 是否存在 `workdir` / `cwd`
- 是否为 `/`
- response status

默认不记录 prompt、源码、命令正文、tool output、Cookie 或 Token。

状态接口：

```text
GET /v1/codex/wire-trace
```

`full` capture 仅供显式本地调试，可能包含私有 prompt、源码和工具输出，严禁提交或上传。

## Required Tool Contract

当用户明确要求：

```text
必须使用 exec_command 执行 pwd
```

或者 harness 使用：

```text
第一步必须通过客户端 exec_command ...
```

V2 都要求 Responses 中真实出现对应 `function_call`。纯文本模拟结果、声称工具不可用、只输出一个路径都不算成功。

首次结果没有真实工具调用时，V2 进行有限 repair。工具真实执行并有匹配 `function_call_output` 后，该 required-tool 已满足，不会因为重建历史里仍包含原始用户要求而再次强制执行。

workspace refusal repair 也会纠正网页模型把“浏览器看不到本机文件系统”误判成“Codex 客户端没有本地工具/工作区”的情况。只有真实客户端工具结果可以证明路径存在与否。

## Root workdir 防护

实机曾出现 Codex turn cwd 正确，但网页模型生成 `workdir="/"`，导致命令落到文件系统根目录。

当前策略：

```text
用户没有明确要求 filesystem root
+
exec-like tool 生成 workdir="/"
→ 删除错误 override
→ Codex 使用自己的 turn cwd
```

UWA 不猜测替代绝对路径。用户明确要求根目录时仍允许 `/`。

## 长进程与 write_stdin

Stage D 已用真实持续进程验证：

```text
exec_command 启动 worker
→ worker 输出 READY 并等待 stdin
→ write_stdin 向同一进程发送 GO\n
→ worker 输出 INTERACTIVE_PASS
→ Codex 继续读取结果
```

wire metadata 中能区分独立 `exec_command` 和 `write_stdin` function call，因此不会把 `echo GO | python ...` 一类 shell 管道误判为持续进程能力。

## Context Compaction

长线程压缩分为两条不同协议路径。

Legacy 路径：

```text
POST /v1/responses/compact
→ ChatGPT Web 生成 replacement-history summary
→ 返回 legacy compact output
```

该路径 P1.1 已通过 direct live。

Codex 0.153.4 remote compaction V2 的真实路径是：

```text
普通 Responses input
+ trailing compaction_trigger
→ POST /v1/responses
→ exactly one type=compaction output item
→ encrypted_content=<opaque transport payload>
```

该普通 Responses V2 路径已完成实现、CI 和真实 macOS native live。实机确认 `REMOTE_COMPACT_ROUTE_DELTA=1`、`REMOTE_COMPACT_SUCCESS_DELTA=1`、`AUTO_COMPACT_MODE=REMOTE`。UWA 使用自己可验证、有限大小的 opaque envelope 做本地兼容状态，不宣称它是 OpenAI encryption。

## Codex Memories

UWA 模式默认关闭 Codex 自动 Memories，避免后台 memory consolidation 抢占唯一受控 ChatGPT tab：

```toml
[memories]
generate_memories = false
use_memories = false
```

helper：

```bash
python3 tools/codex_uwa_memory_guard.py status
python3 tools/codex_uwa_memory_guard.py disable
python3 tools/codex_uwa_memory_guard.py restore
```

项目连续性的长期事实来源仍然是 Git、tracked docs、Codex thread history 和 private Responses state，不依赖 ChatGPT account memory。

## 实机验收矩阵

```text
单文件读 / 改 / 测                       PASS
Stage A 多文件读 / 改 / 测                PASS
Stage B failure recovery                 PASS
Stage C Git diff discipline              PASS
Stage D long process + write_stdin       PASS
Stage E same-thread context              PASS
Stage F Codex + UWA restart              PASS
aggregate A-F checker                    PASS
P1.1 legacy Responses compact            PASS
P1.2 stream / usage / TokenCount         PASS
P1.2 native auto-compact local fallback  PASS
P1.2 remote V2 implementation/CI         PASS
P1.2 UWA provider precondition live      PASS
P1.2 native remote compact macOS live    PASS
P1.2 post-remote same-thread recovery    PASS / CLOSED
P1.3 minimal continuity                  PASS / CLOSED
Hybrid H0-H2                             PASS
Hybrid H3-H5                             CURRENT / mandatory
Desktop reasoning Medium/High            pending / part of UI gate
Desktop UI D1                            PASS / LIVE / CLOSED
Desktop UI D2                            READY / CURRENT
Desktop UI D3-D5                         pending / mandatory
```

操作验收脚本时不要把任务文本写入 zsh 特殊变量，例如 `PROMPT`、`PS1` 或 `PATH`。需要保存 prompt 时使用普通变量名，例如 `ACCEPTANCE_PROMPT`。

## 加速后的 main merge 路线

当前不再用广义 P2-P5 功能扩展阻塞首个稳定 `main`。只保留真正影响正确性和用户可用性的 release-critical gates：

```text
P1.2 same-thread post-remote recovery          PASS / CLOSED
→ P1.3 最小 continuity blockers               PASS / CLOSED
→ Hybrid Routing Safety H0-H5                 H0-H2 PASS / H3-H5 CURRENT
→ Desktop UI D1-D5 + Medium/High reasoning    D1 PASS / D2 CURRENT
→ 一个 real-project long-task pilot
→ final A-F / compaction / restart regression
→ CI + public-repo safety + docs/provenance/license
→ inspect branch topology
→ merge verified V2 to main
```

广义 P2 concurrency/governance、P3 MCP/schema normalization、P4 evidence framework、P5 doctor/preflight 和可选 first-party page-runtime research 移到 `main` 之后继续，除非剩余 live gate 证明某一项必须提前修。

详细决策：`docs/ACCELERATED_MAIN_MERGE_GATE_2026-09-08.md`。

独立仓库阶段不会重写已经工作的 upstream-derived 基础代码。目标是从已验证的 `main` 做依赖审计和核心提取，保留实际需要的 upstream runtime、AGPL-3.0 和明确 attribution，同时去掉与 Codex Web Bridge 无关的通用 UWA 表面积，让后来者更容易安装、理解和使用。详细计划见 `docs/POST_MAIN_STANDALONE_REPOSITORY_PLAN_2026-09-08.md`。

不为了阶段性状态频繁重写 README。详细阶段结果、失败、诊断、实验数据和 checkpoint 应写入 `docs/`，README 只做长期稳定入口；当 release-critical 阶段发生实质变化时同步更新这里的摘要。

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

仓库是 public。禁止提交：

- `.env`
- API Key / Token / 密码
- Cookie / Session / Local Storage
- 浏览器 profile
- UWA / Codex 私有日志
- 私有源码和聊天正文
- `~/.uwa/codex_responses.sqlite3`
- `~/.uwa/debug/codex-wire`
- Codex memory workspace 内容
- 真实 thread / process / browser identifier
- acceptance 捕获的私有 prompt / tool body

## 设计参考与 Attribution

当前仓库本身是 `lumingya/universal-web-api` 的 fork，并实际复用了其浏览器/API/runtime 基础；这部分继续受 upstream AGPL-3.0 与相应 copyright/license 义务约束。

V2 另外研究和借鉴了以下公开项目的设计思路：

- `FlameFront-end/chatgpt-gateway`：浏览器 tool-call round trip 与结构化工具证据，MIT。
- `lininn/codex-proxy`：Responses translation 分层，MIT。
- `mehdic/codex-proxy`：sticky session、TTL、queue、SSE keepalive，MIT。
- OpenAI `codex-responses-api-proxy`：Responses 协议诊断和 paired private dumps，Apache-2.0。
- `yyjeqhc/webcodex`、`Waishnav/devspace`、`XiaoDuoYa/codex-with-chatgpt`、`alexanderradahl/mac-developer-bridge`：身份/lease、MCP/证据治理、doctor/preflight 与 ChatGPT coding bridge 可靠性参考。

除 `lumingya/universal-web-api` 这个实际 upstream 基础外，其他参考项目目前主要作为设计与可靠性研究来源；若未来直接复用任何具体代码，会在对应文件和 attribution 文档中单独标明。

详细来源、许可证、实际复用内容、设计借鉴内容和差异见 `docs/REFERENCES_AND_ATTRIBUTION.md`。

## 项目说明 / 非商业与非官方声明

本仓库维护者当前仅将本项目用于个人学习、个人实验、协议兼容研究、工程验证和非商业用途，不以本项目提供商业化托管、付费代理或账号共享服务。

本项目不是 OpenAI、ChatGPT、Codex、WebCodex 或其他参考项目的官方产品，也不代表这些项目、维护者或公司的认可、合作、授权、代理关系或背书。

本项目不会改变第三方服务本身的账号、订阅、额度或模型开放范围。使用者需要自行确认其账号权限，并自行遵守所使用软件、网站和服务的适用条款、政策与法律要求。

本仓库中的兼容性研究、provider 切换、协议适配和自动化测试仅用于研究本地客户端与已登录网页服务之间的技术互操作性；不构成对任何第三方服务可用性、稳定性、长期兼容性或商业适用性的承诺。
