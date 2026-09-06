# UWA Codex Web Bridge

面向 Codex Desktop / Codex CLI 的本地 ChatGPT Web 推理桥。

目标是保留 Codex 的本地工作区、Shell、测试、Git、sandbox 与 approval 能力，同时把模型推理通过本机 UWA 转发到已登录的 ChatGPT Web。网页模型负责分析和决定工具调用；真正的文件读写、命令、测试和 Git 操作仍由 Codex 客户端在本机权限边界内执行。

当前开发分支：`security-hardening`

## 当前状态

截至 2026-09-06，macOS + Codex Desktop 已实机跑通核心 coding-agent 闭环：

```text
Codex Desktop
-> UWA /v1/responses
-> ChatGPT Web
-> GPT-5.6 Sol / High
-> function_call(exec_command)
-> Codex 本地执行
-> function_call_output
-> 网页模型继续推理
-> 修改文件 / 运行测试
-> 最终汇报
```

已验证：

- 普通文本推理：PASS
- 单文件 `calc.py` 读 / 改 / 测：PASS
- Stage A 多文件读 / 改 / 测：PASS，自动 checker 返回 `ACCEPTANCE_PASS`
- Codex Responses 最小 function-call SSE：PASS
- 多轮 `exec_command -> function_call_output`：已实机工作
- GPT-5.6 Sol / High 网页模式：当前实机路径
- UWA Responses continuation 私有持久化：代码与 CI 完成，重启实机验收仍在 Stage F

Stage B failure-recovery 仍在实机调试。已经确认真实多轮 `exec_command` 可执行；近期问题集中在网页模型后续错误声称 `exec_command` 不存在，以及 Codex 后台 Memories 请求干扰主标签页。

## 架构

```text
Codex Desktop / Codex CLI
        ↓
OpenAI Responses-compatible request
        ↓
UWA 127.0.0.1:8199
        ↓
受控 Chromium / ChatGPT Web
        ↓
GPT-5.6 Sol / High
        ↓
网页模型输出客户端工具调用
        ↓
UWA 转换为 Responses function_call
        ↓
Codex 在本机执行
        ↓
function_call_output 返回 UWA
        ↓
继续下一轮直到完成
```

网页页面本身没有本机文件系统权限。任何本地文件、Shell、测试和 Git 能力都来自 Codex 客户端。

## 模型与推理档位

Codex provider 路由名仍为：

```text
chatgpt
```

当前 UI 目标模型：

```text
GPT-5.6 Sol
```

支持并测试的 reasoning：

```text
Medium
High
```

默认：

```text
GPT-5.6 Sol / High
```

Temporary Chat 目前是 best-effort。项目连续性不依赖 ChatGPT 账号级 Memory。

## 客户端工具调用

UWA 负责：

- Responses / Chat Completions 协议适配
- ChatGPT Web 调度
- 网页流解析
- tool prompt / tool-call 解析与校验
- 网页模型错误拒绝本地工作区时的有限修复
- Responses function_call 输出
- Codex Responses continuation 恢复

Codex 负责：

- 当前工作区
- 本地 Shell
- 文件读写
- 测试
- Git
- sandbox
- approval
- 长进程和 stdin 工具

### 工作区误拒绝修复

网页模型可能错误声称：

```text
无法访问本机文件
当前执行环境没有挂载工作区
exec_command 没有暴露
当前可调用工具中没有 exec_command
```

如果当前请求仍声明客户端工具，且历史已经出现真实工具调用，UWA 会把这些说法视为矛盾并进行有限重试。真实的 `No such file`、权限错误、测试失败等工具结果不会被掩盖；达到重试上限仍 fail closed。

## Codex Responses 最小工具流

Codex 专用工具轮次使用精简 Responses SSE：

```text
response.created
response.output_item.done(function_call)
response.completed
```

当同一轮已经解析到合法 function call 时，网页模型夹带的“没有工具”等矛盾文字不会作为最终答案交给 Codex。

## ChatGPT 网页会话数量

当前复杂 Codex 任务可能在 ChatGPT sidebar 生成多个相似网页对话。

原因是当前每个 Codex tool turn 会重建完整历史并发送给 ChatGPT Web，内部 repair round 也可能增加浏览器请求。不能直接全局关闭“新聊天”，否则完整历史在同一网页会话里重复注入会造成上下文重复。

计划优化：

```text
1. repair round 复用当前失败网页对话
2. 同一 Codex tool loop 建立 web-session affinity
3. 健康映射下只发送新增 tool result / continuation
4. 状态丢失时回退 fresh chat + full reconstructed history
```

## Codex 自动 Memories：UWA 模式暂时隔离

实机发现：前台 Codex 任务结束后，Codex 可能继续启动后台 memory-consolidation 子任务。当前 upstream Codex 的该流程会使用辅助模型，例如 `gpt-5.6-terra`，并操作：

```text
phase2_workspace_diff.md
raw_memories.md
MEMORY.md
memory_summary.md
rollout_summaries/
```

在 custom provider 下，这些后台请求也会进入 UWA，导致：

- Codex 前台看似结束后 ChatGPT Web 仍继续运行
- 后台请求占用受控 ChatGPT 标签页
- 创建额外网页对话
- 消耗延迟和网页模型使用量
- memory Phase 2 遇到工具运行时切换后可能无法安全完成

因此在专门验收完成前，UWA 模式默认策略是关闭 Codex 自动 Memories 的生成与使用：

```toml
[memories]
generate_memories = false
use_memories = false
```

仓库提供安全 helper：

```bash
python3 tools/codex_uwa_memory_guard.py status
python3 tools/codex_uwa_memory_guard.py disable
python3 tools/codex_uwa_memory_guard.py restore
```

`disable` 会备份 `~/.codex/config.toml`，只保存两个开关的原值到 `~/.uwa/codex_memories_guard.json`，不会读取或修改任何 memory 内容。`restore` 用于切回官方 provider 时恢复原值。

详细设计：`docs/CODEX_UWA_MEMORIES.md`。

关闭自动 Memories 不会删除：Codex thread 历史、本地项目文件、Git 状态、现有 memory 文件、UWA continuation DB。

## 连续性设计

项目连续性分三层。

### 1. Codex Desktop thread

Codex Desktop 保存历史 thread。关闭应用不会改变项目文件和 Git。需要延续同一对话时应重新打开同一个 thread。

### 2. UWA Responses continuation

Codex 路径增加私有本地 fallback：

```text
~/.uwa/codex_responses.sqlite3
```

默认：

```text
TTL             7 天
最大条数        4096
单条最大        8 MiB
目录权限        0700（支持时）
DB/WAL/SHM      0600（支持时）
```

查看非内容型状态：

```bash
curl -sS http://127.0.0.1:8199/v1/codex/continuity | python3 -m json.tool
```

此数据库可能含 prompt、源码片段与工具输出，属于本机私有运行态，禁止提交。

### 3. Git checkpoint

长期项目状态以 Git 为准：

- `README.md`
- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`
- `docs/CODEX_UWA_MEMORIES.md`
- Draft PR #1

新 thread / 新对话恢复顺序：

```text
README.md
-> docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md
-> docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md
-> git status
-> git log -5 --oneline
-> relevant diff / tests
```

## 快速开始

```bash
cd ~/universal-web-api
git switch security-hardening
git pull

python3 tools/codex_uwa_memory_guard.py disable

codex-uwa-stop
codex-uwa
```

基础检查：

```bash
curl http://127.0.0.1:8199/health
curl http://127.0.0.1:8199/v1/codex/web-mode
curl http://127.0.0.1:8199/v1/codex/continuity
python3 tools/codex_uwa_memory_guard.py status
```

默认 API Base URL：

```text
http://127.0.0.1:8199/v1
```

## 实机验收

创建独立合成工作区：

```bash
python3 tools/codex_desktop_acceptance.py setup
```

每个 Stage 前：

```bash
python3 tools/codex_desktop_acceptance.py prepare --scenario <scenario>
python3 tools/codex_desktop_acceptance.py preflight --scenario <scenario>
```

查看 prompt：

```bash
python3 tools/codex_desktop_acceptance.py prompts --scenario <scenario>
```

自动判定：

```bash
python3 tools/codex_desktop_acceptance.py check --scenario <scenario>
```

当前矩阵：

```text
单文件 calc.py                       PASS
Stage A 多文件读/改/测                PASS
Stage B failure recovery              rerun after tool-refusal + memory isolation fixes
Stage C Git diff discipline           pending
Stage D long process + write_stdin     pending
Stage E same-thread context             pending
Stage F Codex + UWA restart continuity pending
Codex automatic Memories               isolated / future dedicated acceptance
```

详细步骤：`docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md`。

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

Chromium DevTools 端口可控制受控浏览器，严禁暴露到公网或普通局域网。

仓库为 public。禁止提交：

- `.env`
- API Key / Token / 密码
- Cookie / Session / Local Storage
- 浏览器 profile
- UWA / Codex 私有日志
- 私有源码和聊天正文
- `~/.uwa/codex_responses.sqlite3`
- `~/.uwa/codex_memories_guard.json`
- Codex memory workspace 内容
- 含账号、私有路径、密钥或私有代码的截图

详见 `SECURITY.md`。

## 当前待办

- Stage B 重跑并进入 C-F
- ChatGPT Web tool-loop 增量 continuation / 会话复用
- 完整重启后的 thread continuation
- 长上下文与 compaction
- `write_stdin` / 长进程
- auxiliary request 隔离与路由
- Codex Memories 专项支持
- MCP / namespace tools / plugins / hosted search / multi-agent

## Project history and attribution

仓库保留已有许可证和 Git commit history。当前 README、架构与验收文档描述本 fork 的 Codex Web Bridge 设计与实现；历史作者署名和许可证义务继续保留。当前技术路线与文档按本项目自己的目标维护。
