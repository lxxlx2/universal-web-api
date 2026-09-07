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

首次本机 runtime probe 已确认旧版本 UWA 的实际行为：OpenAPI 没有该 route，直接 POST 返回 `404 Not Found`。

P1.1 已实现 compact endpoint 并通过单元/回归测试与 GitHub Actions Security hardening #220。随后进行的首个 post-implementation macOS live probe 得到：

```text
COMPACT_ROUTE_REGISTERED=YES
COMPACT_HTTP_CODE=500
JSON_PARSE=PASS
OUTPUT_IS_LIST=NO
OUTPUT_COUNT=0
MARKER_PRESERVED=NO
TASK_PRESERVED=NO
```

因此当前结论是：route registration PASS，CI/regression PASS，但真实 compact handler 仍存在未覆盖的运行时异常，P1.1 不能判定 PASS，P1.2 large-context 继续阻塞。当前先提取本机 traceback，补 route-level 回归后再修复，不盲改。

当前顺序：

```text
P1.0 首次 /v1/responses/compact runtime probe       DONE: 404 confirmed
P1.1 compact endpoint 实现 + regression + CI        DONE, CI PASS
P1.1 post-implementation direct compact probe        FAIL: HTTP 500
P1.1 traceback + route-level reproduction + repair   CURRENT
P1.2 synthetic large-context compaction / recovery   BLOCKED
P1.3 lost-affinity / restart fallback 深化验证       pending
Desktop live gate D1-D5                              required before real-project/final merge
P1.4 真实项目长任务 pilot                            pending
P2   并发请求 / queue / controlled-tab 稳定性
P3   MCP / plugin namespace 与 multi-agent / tool fan-out
P4   Responses SSE slimming 与 ChatGPT Web transcript hygiene
P5   final regression / operator docs / release checklist
```

详细记录：

- `docs/CODEX_STAGE_F_RESTART_CONTINUITY_2026-09-07.md`
- `docs/CODEX_FULL_ACCEPTANCE_HARNESS_FALSE_FAILURE_2026-09-07.md`
- `docs/CODEX_P1_RESPONSES_COMPACT_GAP_2026-09-07.md`
- `docs/CODEX_P1_COMPACT_LIVE_500_2026-09-07.md`
- `docs/CODEX_DESKTOP_UI_ACCEPTANCE.md`

## 连续性设计

项目有四层连续性：

1. Codex Desktop / CLI thread history。
2. UWA private Responses persistence：`~/.uwa/codex_responses.sqlite3`。
3. 进程内 ChatGPT web-session / call-id affinity。
4. Git tracked checkpoint，作为跨对话、跨协作者的长期项目事实来源。

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

```bash
cd ~/universal-web-api
git switch codex-web-bridge-v2
git pull
python3 tools/codex_uwa_memory_guard.py disable
codex-uwa-stop
codex-uwa
```

## 切回官方 Codex Desktop / ChatGPT 账号模式

这个操作的目标只是恢复 Codex 的正常官方账号模式。**不固定模型，不固定 reasoning，不限制 Astra 或其他模型。** 完成后在 Codex Desktop 的模型选择器里正常选择当前账号/工作区可用的任意模型即可。

先停止 UWA，并移除 `~/.codex/config.toml` 顶层由 UWA 使用的 provider/model/reasoning 固定项：

```bash
cd ~/universal-web-api
codex-uwa-stop
python3 tools/codex_provider_switch.py official
python3 tools/codex_uwa_memory_guard.py restore
```

`codex_provider_switch.py official` 会先备份当前 `~/.codex/config.toml`，然后只清理顶层 `model_provider`、`model`、`model_reasoning_effort` 固定项；它保留 `[model_providers.uwa]` 定义，也不会修改登录凭据。

随后：

1. 完全退出 ChatGPT Desktop / Codex。
2. 重新打开 Desktop。
3. 如果客户端提示登录，使用自己的 ChatGPT 账号登录。
4. 在 Codex 中正常选择 Astra 或任何当前账号可用模型。

查看当前是否仍存在顶层固定项：

```bash
cd ~/universal-web-api
python3 tools/codex_provider_switch.py status
```

再次切回 UWA 时无需删除官方账号：

```bash
cd ~/universal-web-api
python3 tools/codex_uwa_memory_guard.py disable
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

这些项目用于设计研究和协议理解，不表示其作者对本项目的认可或背书。除非具体提交另有说明，V2 当前代码按本仓库设计独立实现，没有直接复制上述参考项目的源文件。详细来源、许可证、借鉴点和 copying policy 见 `docs/REFERENCES_AND_ATTRIBUTION.md`。

## 安全边界

仓库是 public。不要提交浏览器 profile、Cookie、Local Storage、credentials、私有日志、full wire trace、Responses SQLite、真实 thread/process/browser identifiers、Codex memory workspace 内容或私有项目源码。

设计参考与许可证说明见 `docs/REFERENCES_AND_ATTRIBUTION.md`。
