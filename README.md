# UWA Codex Web Bridge V2

面向 Codex Desktop / Codex CLI 的本地 ChatGPT Web 推理桥。

当前开发分支：`codex-web-bridge-v2`。

## 项目目标

保留 Codex 的本地工作区、Shell、文件修改、测试、Git、sandbox 与 approval 能力，同时把模型推理通过本机 UWA 转发到已登录的 ChatGPT Web。网页模型负责分析和选择客户端工具，真实本地操作仍由 Codex 客户端执行。

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
单文件读/改/测                         PASS
Stage A 多文件读/改/测                  PASS
Stage B failure recovery               PASS
Stage C Git diff discipline            PASS
Stage D long process + write_stdin     PASS
Stage E same-thread context            PASS
Stage F Codex + UWA restart            PASS
A-F aggregate checker                  PASS
真实 exec_command / native cwd         PASS
Responses tool round trip              PASS
required-tool enforcement              PASS
call-id / web-session continuation     PASS
P1.1 Responses compact live            PASS
versioned UWA lifecycle CI             PASS
versioned UWA lifecycle live           PASS
versioned UWA provider switch CI       PASS
versioned UWA provider switch live     PASS
P1.2 large-context compaction/recovery CURRENT
Codex Desktop UI live gate             REQUIRED BEFORE MAIN MERGE
```

Stage F 已验证真实 UWA 重启后的连续性：重启前进程内 affinity 存在，重启后 `binding_count=0`，同一 Codex thread 仍可恢复上下文并继续真实本地工具执行，最终独立 checker 返回 `ACCEPTANCE_PASS`。

需要特别区分：Stage E/F 的最终可审计实机证据主要来自 `codex exec / resume` CLI。它证明了 Codex 协议、线程恢复、本地工具和 UWA restart 链路，但不能替代 Codex Desktop UI 本身的最终验收。因此项目新增独立 Desktop live gate，并把它纳入 `main` 合并门槛。

## Aggregate regression

Stage F 收口后的第一次完整 checker 曾出现 `git_diff: FAIL`。当时 `values_ok=True`、`diff_check=0`，失败来源是 `PROMPTS.md`、`__pycache__` 和 `.pyc` 等 harness/runtime artifacts。该问题已确认是 Stage C aggregate checker 的假失败，并通过窄范围修复解决。

修复后在同一个真实 acceptance workspace 中直接重跑：

```text
multi_file: PASS
failure_recovery: PASS
git_diff: PASS
interactive: PASS
context: PASS
ACCEPTANCE_PASS
```

因此 A-F aggregate regression 已正式关闭为 PASS。

## P1 large-context 当前入口

上游 Codex 在 remote compaction 时会调用：

```text
POST /v1/responses/compact
```

P1.0 首次实机检查确认旧版本 UWA 没有该 route，直接 POST 返回 `404 Not Found`。P1.1 随后实现 compact endpoint，并补充 route-level regression。

第一次 post-implementation macOS probe 暴露了 `SecureLogger.info()` 调用签名问题；修复后 CI PASS。随后又发现普通 `codex-uwa-stop` / `codex-uwa` 流程没有真正替换 TCP 8199 上的旧 listener，导致请求继续命中修复前加载的旧 bytecode。

在验证 listener cwd 后强制清空 8199、启动新的 UWA PID，再运行完全相同的 compact probe，最终实机结果为：

```text
PORT_8199_EMPTY=YES
LISTENER_REPLACED=YES
COMPACT_HTTP_CODE=200
JSON_PARSE=PASS
OUTPUT_IS_LIST=YES
OUTPUT_COUNT=1
OUTPUT_0_TYPE=message ROLE=assistant
MARKER_PRESERVED=YES
TASK_PRESERVED=YES
```

因此 P1.1 compact protocol 已正式 PASS。

旧 `~/bin/codex-uwa*` 脚本随后被确认存在两个 lifecycle 缺陷：`codex-uwa-stop` 发送 TERM 后没有验证 8199 是否真的为空；`codex-uwa` 只要 `/health` 正常就复用现有进程，因此 `git pull` 后也可能继续使用旧 bytecode。生命周期逻辑现已迁回仓库：

- `tools/codex_uwa_lifecycle.py`：以真实 8199 listener + cwd 为准，TERM → 等待 → 必要时 KILL → 必须确认端口为空；restart 必须产生新的 listener PID 并通过 `/health`。
- `tools/install_codex_uwa_commands.py`：把 `~/bin/codex-uwa` 与 `~/bin/codex-uwa-stop` 安装为薄 wrapper，核心逻辑始终从当前 Git checkout 执行。
- `codex-uwa` wrapper 自动关闭 UWA 模式下的 Codex Memories，不再要求用户手工先执行 memory guard。
- lifecycle / wrapper regression 与 CI PASS。

真实 macOS wrapper 安装和 stop/restart 也已经通过：

```text
STOPPED_LISTENERS=57575
PORT_EMPTY=YES
PORT_8199_EMPTY=YES
OLD_PID=57575
NEW_PID=67555
LISTENER_REPLACED=YES
NEW_CWD=/Users/jerson/universal-web-api
SERVICE=healthy
BROWSER_CONNECTED=True
HEALTH_PASS=YES
VERSIONED_LIFECYCLE_PASS
```

因此 stale-runtime lifecycle blocker 已正式关闭。详细记录：`docs/CODEX_UWA_LIFECYCLE_LIVE_2026-09-07.md`。

最后一个 Git 外执行依赖 `~/.uwa/config_switch.py uwa` 也已经迁回仓库。`tools/codex_provider_switch.py uwa` 现在管理 UWA provider 合同，`codex-uwa` thin wrapper 不再引用旧 helper。CI #289 完整 PASS，真实 macOS 验收同时证明：无关 Codex 配置保持、UWA root/provider 合同正确、restore state 存在、listener 真正换新且健康检查通过。详细记录：`docs/CODEX_UWA_PROVIDER_SWITCH_MIGRATION_2026-09-08.md`。

验收脚本里曾出现一次本机 focused pytest 假 PASS：本机 `venv` 缺 pytest，测试实际未执行，但后续无条件 `echo FOCUSED_TESTS=PASS`。该 echo 不计入证据；provider/wrapper 回归证据来自已成功的 CI #289，真实切换证据来自 macOS live run。

当前正式进入 P1.2：测试重点是同一 Codex thread 的大上下文增长、native `/v1/responses/compact`、关键事实恢复和机器可审计证据，而不是简单读取一个大文件。只有观察到明确 compact route/lifecycle 证据时才宣称 compaction PASS；否则只归类为 large-context stress/recovery。

当前顺序：

```text
P1.0 /v1/responses/compact runtime gap               DONE: 404 confirmed
P1.1 compact endpoint + regressions                  PASS
P1.1 macOS fresh-listener direct compact             PASS: HTTP 200
P1.1 versioned lifecycle implementation + CI         PASS
P1.1 versioned lifecycle macOS live validation       PASS
P1.1 versioned UWA provider switch + live            PASS
P1.2 native Codex large-context compaction/recovery  CURRENT
P1.3 affinity/restart + identity fencing + uncertain-effect recovery
Desktop live gate D1-D5                              required before real-project/final merge
P1.4 真实项目长任务 pilot                            pending
P2   per-continuation serialization / queue planes / controlled-tab stale-result hardening
P3   MCP/plugin namespace + capability fidelity + multi-agent/tool fan-out
P4   Responses SSE slimming + bounded trace/transcript hygiene
P5   runtime/build identity + compatibility preflight + final regression/release checklist
```

详细记录：

- `docs/CODEX_STAGE_F_RESTART_CONTINUITY_2026-09-07.md`
- `docs/CODEX_FULL_ACCEPTANCE_HARNESS_FALSE_FAILURE_2026-09-07.md`
- `docs/CODEX_P1_RESPONSES_COMPACT_GAP_2026-09-07.md`
- `docs/CODEX_P1_COMPACT_LIVE_500_2026-09-07.md`
- `docs/CODEX_UWA_LIFECYCLE_LIVE_2026-09-07.md`
- `docs/CODEX_UWA_PROVIDER_SWITCH_MIGRATION_2026-09-08.md`
- `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`
- `docs/WEBCODEX_ARCHITECTURE_REVIEW_2026-09-07.md`

## 连续性设计

项目有四层连续性：

1. Codex Desktop / CLI thread history。
2. UWA private Responses persistence：`~/.uwa/codex_responses.sqlite3`。
3. 进程内 ChatGPT web-session / call-id affinity。
4. Git tracked checkpoint，作为跨对话、跨协作者的长期项目事实来源。

WebCodex 研究进一步强化了一个约束：Codex thread、Responses `response_id`、tool `call_id`、ChatGPT Web conversation、UWA 进程、受控 tab 和 Codex 本地执行状态是不同身份域。后续 P1.3 会把“请求丢失不等于执行丢失”“不确定 effect 不允许盲重试”“旧进程/tab generation 不得向新 continuation 提交结果”加入正式验收。

## 协作规则

每个 live acceptance 结果、重要失败、关键修复和阶段切换都要在进入下一步前同步到 Git。至少维护 README、canonical current state、progress、对应 stage/failure record，以及必要时更新 Draft PR。

## 合并到 main 的门槛

`codex-web-bridge-v2` 暂不合并。需要全部满足：

1. aggregate A-F regression PASS；
2. compact protocol、large-context 与 lost-affinity/restart recovery 无阻断问题；
3. Codex Desktop UI live gate PASS；
4. 至少一次真实项目长任务 pilot PASS；
5. CI 全绿；
6. README、current-state、progress、operator docs、release checklist 同步；
7. public repository safety 检查通过。

## Codex Memories

UWA 验收模式继续关闭 Codex 自动 Memories：

```toml
[memories]
generate_memories = false
use_memories = false
```

## 快速启动 UWA

首次把本机命令切换为仓库受控的薄 wrapper：

```bash
cd ~/universal-web-api
git switch codex-web-bridge-v2
git pull
python3 tools/install_codex_uwa_commands.py
codex-uwa
```

安装一次后，日常进入 UWA 模式只需要：

```bash
codex-uwa
```

`codex-uwa` 会自动关闭 UWA 模式下的 Codex Memories、通过仓库版 `codex_provider_switch.py uwa` 切换 provider、退出 Codex Desktop、执行可验证的 UWA restart、确认新 listener 与 `/health`，然后重新打开 Codex Desktop。`codex-uwa-stop` 会在确认 listener 属于当前仓库后停止真实 8199 listener，并且只有端口确实为空才返回成功。

正常 UWA 启动路径已经不依赖 `~/.uwa/config_switch.py`。旧 helper 可以保留在本机作为历史文件，但不会被 versioned wrapper 执行。

## 一键切回官方 Codex Desktop / ChatGPT 账号模式

这个操作只恢复 Codex 的正常官方账号模式。**不固定模型，不固定 reasoning，不限制 Astra 或其他模型，也不修改登录凭据。** 切换完成后可以直接使用账号默认模型，或在 Codex Desktop 的模型选择器中选择当前账号/工作区可用的任意模型。

正常使用只需要一条命令：

```bash
cd ~/universal-web-api
python3 tools/codex_provider_switch.py official
```

`official` 默认自动完成以下动作，无需手工退出或重新打开 Desktop：

1. 自动退出正在运行的 ChatGPT Desktop / Codex；
2. 检查 TCP `8199` 的真实 listener，只在 listener cwd 与当前 UWA 仓库一致时自动停止它，避免误杀其他进程；
3. 自动恢复进入 UWA 模式前保存的 Codex Memories 设置；
4. 恢复 UWA 临时覆盖的非模型 policy/context/catalog 值，并清理顶层 `model_provider`、`model`、`model_reasoning_effort` 固定项；
5. 保留 `[model_providers.uwa]` 定义和现有账号认证状态；
6. 自动重新打开 ChatGPT Desktop；若未安装 ChatGPT.app，则尝试打开独立 Codex.app。

成功时会输出类似：

```text
OFFICIAL_MODE_CHANGED=YES
UWA_LISTENER_STOPPED=<pid-or-NONE>
DESKTOP_APPS_STOPPED=ChatGPT
DESKTOP_REOPENED=ChatGPT
AUTH=UNCHANGED
MODEL_SELECTION=ACCOUNT_DEFAULT_UI
```

如果脚本无法确认 8199 listener 属于当前仓库，它会直接失败并拒绝杀进程；如果系统无法找到 ChatGPT/Codex Desktop，也会明确返回错误，而不是假装切换成功。

查看当前是否仍存在顶层固定项：

```bash
cd ~/universal-web-api
python3 tools/codex_provider_switch.py status
```

用于 CI、调试或特殊场景时，可以显式关闭部分自动化：

```bash
python3 tools/codex_provider_switch.py official --no-desktop-restart
python3 tools/codex_provider_switch.py official --no-stop-uwa
```

再次切回 UWA 时无需删除或退出官方账号：

```bash
codex-uwa
```

## 项目说明与责任边界

本项目是个人实验、协议兼容研究和工程验证项目，不是 OpenAI、ChatGPT、Codex 或任何参考项目的官方产品，也不代表这些项目或公司的认可、合作、授权或背书。

责任边界如下：

- UWA 负责本机浏览器交互、协议适配和 Responses/Web bridge；第三方网页、模型、账户和服务由对应服务提供方控制。
- ChatGPT Web 负责模型推理和工具选择；真实 filesystem、Shell、测试、Git 等本地操作仍由 Codex 客户端在其 sandbox / approval 边界内执行。
- 项目作者只对本仓库中自行维护的代码、文档和已记录测试结果负责，不保证第三方网页结构、模型目录、账号资格、配额、速率限制、接口兼容性或持续可用性。
- 使用者负责自己的账号、Cookie、凭据、数据、网络环境、当地法律法规、第三方服务条款、隐私与安全策略，以及对本地或线上环境执行操作前的授权和备份。
- 请勿将本项目用于绕过付费墙、账号限制、访问控制、平台条款、安全机制或其他本无权访问的资源。
- 对账号限制或封禁、额度/费用变化、第三方服务中断、数据丢失、代码或系统损坏、知识产权争议、合规风险及其他直接或间接损失，作者不提供保证或赔偿承诺。
- 在真实项目使用前，应先在隔离 worktree、测试仓库或本项目 acceptance workspace 中完成验证，并自行保留可恢复备份。

## 发布目的、许可证与使用立场

本仓库公开的主要目的为个人作品展示、学习、技术研究、协议兼容性验证和可复现工程记录。作者不提供商业 SLA、商业部署承诺或商业合规背书，也不鼓励把本项目包装成未经授权的第三方付费服务。

本仓库继承上游 `lumingya/universal-web-api` 的 Git 历史和 **AGPL-3.0** 许可证。许可证文本是法律许可范围的最终依据。AGPL-3.0 本身允许在满足其条件的前提下进行商业使用，因此这里关于“展示、学习和研究”的说明属于作者的发布目的和使用立场，不构成对 AGPL-3.0 已授予权利的额外限制。

任何商业使用者必须自行确认并承担全部合规责任，包括但不限于：

- AGPL-3.0 的源码提供、修改披露及网络服务相关义务；
- 上游项目和第三方代码的版权、许可证与归属要求；
- OpenAI、ChatGPT、Codex 以及实际接入网站/服务的使用条款和账户规则；
- 当地适用的法律、数据保护、隐私、安全、消费者保护及商业监管要求。

未经单独书面约定，作者不提供商业授权承诺、商业支持、担保、赔偿或对第三方商业用途的认可。若未来希望在法律层面为作者独立拥有的新增材料设置真正的“非商业”许可，需要另行完成版权归属、上游 AGPL 兼容性和许可结构审查，不能仅通过 README 改写现有 AGPL-3.0 权利。

## 致谢与参考项目

本项目建立在开源社区已有工作之上，感谢相关作者和贡献者：

- [`lumingya/universal-web-api`](https://github.com/lumingya/universal-web-api)：本仓库的上游基础，提供浏览器控制、站点抽象和 OpenAI-compatible API 等核心能力。
- [`FlameFront-end/chatgpt-gateway`](https://github.com/FlameFront-end/chatgpt-gateway)：参考 browser ChatGPT gateway、结构化 tool/function round trip、parser validation 与多轮 tool-result continuation 等思路。
- [`lininn/codex-proxy`](https://github.com/lininn/codex-proxy)：参考独立 Responses compatibility boundary、请求/响应/SSE translator 分层设计。
- [`mehdic/codex-proxy`](https://github.com/mehdic/codex-proxy)：参考 sticky session、TTL/LRU、同一逻辑会话串行化和 SSE keepalive 等设计。
- [`openai/codex`](https://github.com/openai/codex) 及其 Responses proxy 相关实现：参考 Codex Responses 协议边界、诊断 trace、correlation、redaction 和本地调试隔离方式。
- [`yyjeqhc/webcodex`](https://github.com/yyjeqhc/webcodex)：参考 request-loss 与 execution-loss 分离、uncertain-effect recovery、稳定身份与进程 generation 分离、bounded observation、MCP/schema/capability discipline、并发与恢复验收设计；V2 不复制其 Runner，而继续由官方 Codex 负责本地执行。

这些项目用于设计研究和协议理解，不表示其作者对本项目的认可或背书。除非具体提交另有说明，V2 当前代码按本仓库设计独立实现，没有直接复制上述参考项目的源文件。详细来源、许可证、借鉴点和 copying policy 见 `docs/REFERENCES_AND_ATTRIBUTION.md`。

## 安全边界

仓库是 public。不要提交浏览器 profile、Cookie、Local Storage、credentials、私有日志、full wire trace、Responses SQLite、真实 thread/process/browser identifiers、Codex memory workspace 内容或私有项目源码。

设计参考与许可证说明见 `docs/REFERENCES_AND_ATTRIBUTION.md`。
