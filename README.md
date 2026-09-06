# UWA Codex Web Bridge

一个面向 Codex Desktop / Codex CLI 的本地浏览器模型桥接项目。

目标：保留 Codex 的本地工作区、Shell、测试、Git、sandbox 与 approval 能力，同时把模型推理请求通过本机 UWA 转发到已经登录的 ChatGPT 网页。网页模型负责分析和决定工具调用，真正的本地文件与命令操作继续由 Codex 客户端执行。

当前开发分支：`security-hardening`

## 当前状态

截至 2026-09-06，核心 coding-agent 闭环已经在 macOS + Codex Desktop 实机跑通：

```text
Codex Desktop
-> UWA /v1/responses
-> ChatGPT Web
-> GPT-5.6 Sol / High
-> function_call(exec_command)
-> Codex 本地执行
-> function_call_output
-> 网页模型继续推理
-> 修改文件
-> 运行测试
-> 最终汇报
```

已通过两类真实验收：

- 单文件 `calc.py`：读取、修改、实际断言测试通过
- Stage A 多文件：修改两个实现文件、未修改测试、3 个 unittest 全部通过，自动检查返回 `ACCEPTANCE_PASS`

Stage B 已暴露两类问题并都已记录：

1. 第一次尝试的 Codex 工作区没有指向合成验收目录，该次归类为 `INVALID`；验收工具已经增加 scenario 级 `prepare`、`preflight` 和工作区 marker。
2. 第二次尝试已经在正确工作区连续执行了多轮真实 `exec_command`，但后续网页模型错误声称“当前实际可调用工具中没有名为 `exec_command` 的客户端工具”。当前分支已经扩展 post-tool contradiction policy，并增加精确回归测试，等待 Stage B 再次实机验收。

当前重点已经从“能不能工作”进入“多轮稳定性、连续性、网页会话效率和高级工具兼容”。

## 架构

```text
Codex Desktop / Codex CLI
        ↓
OpenAI Responses-compatible request
        ↓
UWA 127.0.0.1:8199
        ↓
ChatGPT Web preflight
        ↓
GPT-5.6 Sol / Medium-High
        ↓
受控 Chromium
        ↓
网页模型输出客户端工具调用
        ↓
UWA 转换为 Responses function_call
        ↓
Codex 在本机权限边界内执行
        ↓
function_call_output 返回 UWA
        ↓
网页模型继续下一轮
```

网页页面本身没有本机文件系统权限。`exec_command`、文件读写、测试与 Git 操作仍由 Codex 客户端负责。

## 模型与推理档位

Codex 内部逻辑路由仍使用：

```text
chatgpt
```

Codex UI 显示目标模型：

```text
GPT-5.6 Sol
```

当前桥接层支持：

```text
Medium
High
```

默认：

```text
GPT-5.6 Sol / High
```

当前实机验收使用的是 `GPT-5.6 Sol / High`。

Temporary Chat 仍会优先尝试开启，但当前 ChatGPT DOM 对 Temporary Chat 状态的可观察性不稳定，所以它暂时是 best-effort，不作为项目连续性的依赖条件。

## 本地工具调用

UWA 负责：

- Responses / Chat Completions 协议适配
- ChatGPT 网页调度
- 网页流解析
- 工具调用提示与解析
- 网页模型误拒绝本地工作区时的有限纠错
- Responses function_call 输出
- Codex continuation 运行态恢复

Codex 负责：

- 当前工作区
- 本地 Shell
- 文件读取与修改
- 测试
- Git
- sandbox
- approval
- 长进程及客户端工具执行

### 工作区误拒绝修复

网页模型可能错误回答：

```text
我无法访问你的本机文件
当前会话没有挂载本地工作区
exec_command 没有暴露
当前实际可调用工具中没有名为 exec_command 的客户端工具
```

如果 Codex 当前请求仍声明客户端工作区工具，UWA 会把这类回答视为错误决策，进行有限次数的聚焦修复，要求模型输出真实工具调用。

在已经发生过真实 `exec_command` 的多轮历史中，工具可用性由“当前请求声明的 tools + 已发生的客户端工具历史”共同证明，不再依赖最新 user-shaped item 仍然像原始工作区任务。这个变化专门处理 Codex 把 tool result 编码成后续 user item 的情况。

真实的文件不存在、权限不足、测试失败等客户端结果不会被覆盖；修复次数耗尽仍然 fail closed。

## Codex Responses 最小工具流

为提高 Codex Desktop 对 custom provider 的兼容性，工具轮次使用精简 Responses SSE：

```text
response.created
response.output_item.done(function_call)
response.completed
```

网页模型夹带“没有工具”等矛盾文字时，只要同一轮已经解析出合法 function call，这些中间文字不会作为最终回答交给 Codex。

## ChatGPT 网页会话与多轮工具循环

当前一个复杂 Codex 任务可能在 ChatGPT 网页侧创建多个相似对话。这是现阶段通用 UWA 工作流的已知副作用。

当前每个 Codex Responses tool turn 都会重建完整历史并发送给 ChatGPT Web。通用浏览器工作流默认倾向新建网页对话，因此多轮 `exec_command -> function_call_output -> 下一轮` 会产生多条 ChatGPT sidebar 记录；内部 repair round 还会增加额外浏览器请求。

不能简单全局关闭“新聊天”：当前 outer turn 带的是完整重建历史，如果在同一个 ChatGPT 网页对话里反复发送完整历史，会造成上下文重复。

后续安全优化顺序：

```text
1. repair round 复用刚才失败的同一个网页对话
2. Codex tool loop 建立 web-session affinity
3. 健康映射下只发送新增 tool result / continuation
4. UWA/浏览器重启、映射丢失或页面异常时回退到 fresh chat + full reconstructed history
```

在这个优化完成前，多条网页 sidebar 对话主要是性能与 UX 问题，不影响 Codex 本地工具权限边界。

## 对话、记忆与长期连续性

项目把连续性拆成三层。

### 1. Codex Desktop thread 历史

Codex Desktop 会保留历史 thread，关闭应用不会改变本地项目文件或 Git 状态。需要延续同一个对话时，应重新打开同一个 thread。

完全关闭/重开 Desktop 后能否无损恢复同一 thread，正在 Stage F 做专门实机验收。

### 2. UWA 私有 Responses continuation

通用 Responses 层原来的 `previous_response_id` 状态只存在 Python 内存中：

```text
最多 1024 条
TTL 1 小时
UWA 重启后消失
```

Codex 路径现在增加私有本地 SQLite fallback：

```text
~/.uwa/codex_responses.sqlite3
```

默认：

```text
保留时间      7 天
最大条数      4096
单条最大      8 MiB
目录权限      0700（系统支持时）
DB/WAL/SHM    0600（系统支持时）
```

它可能包含 prompt、源码片段和工具输出，只属于本机运行态，禁止提交或上传。

查看非内容型状态：

```bash
curl -sS http://127.0.0.1:8199/v1/codex/continuity | python3 -m json.tool
```

如果 UWA 内存里的 `previous_response_id` 因重启或过期而消失，Codex 专用路由会尝试从这个私有数据库恢复；如果客户端已经带来了可重放的完整历史，也允许从客户端历史继续。缺少匹配历史的 delta-only 工具结果仍然会 fail closed。

### 3. Git 中的项目 checkpoint

长期进度不能只依赖模型记忆。

本项目把以下文件作为正式交接源：

- `README.md`
- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`
- Draft PR #1 的时间线记录

如果当前聊天或 Codex thread 到达上下文上限，新对话应先读取这些文件和当前 Git 状态再继续。

推荐恢复顺序：

```text
README.md
-> docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md
-> docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md
-> git status
-> git log -5 --oneline
-> 当前相关 diff / tests
```

ChatGPT 账号级 Memory 不作为项目事实源。

## 快速开始

更新当前开发分支：

```bash
cd ~/universal-web-api
git switch security-hardening
git pull
```

后台重启 UWA：

```bash
codex-uwa-stop
codex-uwa
```

基础检查：

```bash
curl http://127.0.0.1:8199/health
curl http://127.0.0.1:8199/v1/codex/web-mode
curl http://127.0.0.1:8199/v1/codex/continuity
```

默认 API Base URL：

```text
http://127.0.0.1:8199/v1
```

## 推荐本地配置

```env
APP_HOST=127.0.0.1
APP_PORT=8199
APP_DEBUG=false
CORS_ENABLED=false
CMD_ALLOW_UNSAFE_PYTHON_COMMANDS=false
AUTO_UPDATE_ENABLED=false
UWAPI_ALLOW_REMOTE=false

TOOL_CALLING_CLIENT_WORKSPACE_REPAIR=true
TOOL_CALLING_PROMPT_PADDING_ENABLED=false
TOOL_CALLING_PROMPT_PADDING_OBFUSCATE=false

UWA_CODEX_WEB_MODE_ENABLED=true
UWA_CODEX_WEB_MODE_STRICT=true
UWA_CODEX_WEB_MODEL=GPT-5.6 Sol
UWA_CODEX_REASONING_DEFAULT=high
UWA_CODEX_TEMPORARY_CHAT=true
UWA_CODEX_TEMPORARY_CHAT_STRICT=false

UWA_CODEX_RESPONSES_PERSIST=true
UWA_CODEX_RESPONSES_STATE_TTL_SEC=604800
UWA_CODEX_RESPONSES_STATE_MAX_ENTRIES=4096
UWA_CODEX_RESPONSES_STATE_MAX_RECORD_BYTES=8388608
```

完整模板见 `.env.example`。

## 实机验收

首次创建独立测试工作区：

```bash
python3 tools/codex_desktop_acceptance.py setup
```

每一阶段开始前，先重置并校验该 scenario：

```bash
python3 tools/codex_desktop_acceptance.py prepare --scenario failure_recovery
python3 tools/codex_desktop_acceptance.py preflight --scenario failure_recovery
```

`prepare` 只重置目标 scenario，并保留其他 Stage 的本地结果。整个验收目录丢失时，它会安全重建带 marker 的合成工作区。`preflight` 会检查 marker、Git 根目录、目标目录和预期初始状态。

查看验收 prompt：

```bash
python3 tools/codex_desktop_acceptance.py prompts
```

自动判定结果：

```bash
python3 tools/codex_desktop_acceptance.py check
```

当前矩阵：

```text
单文件 calc.py                  PASS
Stage A 多文件读/改/测           PASS
Stage B 失败 -> 修复 -> 重跑      rerun after repeated tool-list refusal fix
Stage C Git diff discipline      pending
Stage D 长进程 + write_stdin      pending
Stage E 同 thread 上下文          pending
Stage F 关闭/重开 Codex + UWA     pending
```

详细步骤见 `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md`。

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

Chromium DevTools 默认端口 `9222` 可以控制整个受控浏览器会话，严禁暴露到公网或普通局域网。

这个仓库是 public repository。禁止提交：

- `.env`
- API Key、Token、密码
- Cookie、Session、Local Storage
- 浏览器 profile
- UWA / Codex 私有日志
- 私有项目源码或聊天原文
- `~/.uwa/codex_responses.sqlite3`
- 任何 Responses runtime database
- 含账号、路径、密钥或私有代码的截图

详细规则见 `SECURITY.md`。

## 当前限制

仍需验证或实现：

- Stage B 重跑与后续 C-F 实机验收
- UWA + Codex 完整重启后的 thread continuation
- ChatGPT 网页会话 churn / 增量 continuation
- 长上下文和 compaction
- token/context 近似计量
- `write_stdin` 和长进程稳定性
- MCP
- namespace tools
- plugins
- hosted search
- multi-agent / subagents

## Project history and attribution

The repository preserves its existing license and Git history. The active README, architecture and acceptance documents describe this fork's current Codex web-bridge design and implementation. Historical commit authorship and license obligations remain intact; the current documentation is maintained around this project's own architecture rather than copying the previous project's feature-tour documentation.
