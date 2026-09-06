# UWA Codex Web Bridge

面向 Codex Desktop / Codex CLI 的本地 ChatGPT Web 推理桥。

目标：保留 Codex 的本地工作区、Shell、文件修改、测试、Git、sandbox 与 approval 能力，同时把模型推理通过本机 UWA 转发到已登录的 ChatGPT Web。网页模型负责分析与选择客户端工具；真正的本地操作仍由 Codex 客户端执行。

当前开发分支：`security-hardening`

## 当前状态

截至 2026-09-06，macOS 实机已跑通核心 coding-agent 闭环：

```text
Codex Desktop / CLI
-> UWA /v1/responses
-> ChatGPT Web
-> GPT-5.6 Sol / High
-> function_call(exec_command)
-> Codex 本地执行
-> function_call_output
-> 网页模型继续推理
-> 修改 / 测试 / 最终汇报
```

已验证：

- 普通文本推理：PASS
- 单文件读 / 改 / 测：PASS
- Stage A 多文件读 / 改 / 测：PASS，自动 checker 返回 `ACCEPTANCE_PASS`
- Codex Responses 最小 function-call SSE：PASS
- 多轮 `exec_command -> function_call_output`：实机已工作
- GPT-5.6 Sol / High：当前实机目标路径
- UWA Responses continuation 私有持久化：代码与 CI 完成，重启实机验收在 Stage F
- root workdir 防护：代码与回归完成
- 显式声明的客户端工具被网页模型错误声称“不可用”时的有限修复：代码与回归完成

Stage B failure-recovery 仍在实机验收。当前先用短 CLI 探针确认工作目录继承与客户端工具调用稳定，再恢复完整 Stage B。

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
UWA 校验并转换为 Responses function_call
        ↓
Codex 在本机执行
        ↓
function_call_output 返回 UWA
        ↓
继续下一轮直到完成
```

网页页面自身没有本机文件系统权限。本地文件、Shell、测试和 Git 能力都来自 Codex 客户端。

## 客户端工具兼容策略

网页模型有时会错误声称：

```text
无法访问本机文件
当前执行环境没有挂载工作区
exec_command 没有暴露
当前可调用工具中没有 exec_command
exec_command 不可用
```

当当前请求明确声明客户端工具时，UWA 会把这类与工具声明矛盾的回复纳入有限修复。已有真实工具历史时，后续再声称同一工具不存在同样会被拦截。真实的 `No such file`、权限错误和测试失败不会被覆盖；达到内部重试上限仍 fail closed。

显式出现 `exec_command`、`shell_command`、`local_shell`、`apply_patch` 或 `write_stdin` 的用户请求会被视为本地客户端工具任务，因此最小探针，例如“使用 `exec_command` 执行 `pwd`”，也能触发上述保护。

### Root workdir 防护

实机探针曾出现：Codex turn cwd 正确，但网页模型生成的 `exec_command` 显式带了 `workdir="/"`，导致实际命令落到文件系统根目录。

当前策略：

```text
用户未明确要求 filesystem root
+
exec_command / shell_command / local_shell 生成 workdir="/"
↓
UWA 拒绝该候选
↓
要求保留原命令并省略 workdir
↓
Codex 继承当前 turn cwd
```

UWA 不会把 `/` 自动替换成猜测的绝对路径。用户明确要求根目录时仍允许 `workdir="/"`。重复强制 root 超过修复上限时 fail closed。

回归覆盖：

- `tests/test_client_tool_policy_root_workdir.py`
- `tests/test_client_tool_policy_repeated_refusal.py`
- `tests/test_client_tool_policy.py`

最新兼容修复 CI：Security hardening #122，6 个 job 全部通过，包括完整 upstream regression。

## Codex Responses 最小工具流

Codex 专用工具轮次使用精简 Responses SSE：

```text
response.created
response.output_item.done(function_call)
response.completed
```

当同一轮已经解析到合法 function call 时，网页模型夹带的矛盾文字不会作为最终答案交给 Codex。

## ChatGPT 网页会话数量

当前复杂 Codex 任务可能在 ChatGPT sidebar 生成多个相似对话。当前每个 Codex tool turn 会重建历史并发送给 ChatGPT Web，内部 repair round 也可能增加浏览器请求。

计划优化顺序：

```text
1. repair round 复用当前失败网页对话
2. 同一 Codex tool loop 建立 web-session affinity
3. 健康映射下只发送新增 tool result / continuation
4. 状态丢失时回退 fresh chat + reconstructed history
```

在增量 continuation 完成前，不直接全局复用同一个网页对话，避免把完整历史重复注入。

## Codex 自动 Memories：UWA 模式暂时隔离

实机发现 Codex 前台任务结束后可能继续启动 memory-consolidation 子任务。这些后台请求也会进入 custom provider，抢占受控 ChatGPT 标签页并产生额外网页会话。

UWA 模式当前关闭：

```toml
[memories]
generate_memories = false
use_memories = false
```

仓库 helper：

```bash
python3 tools/codex_uwa_memory_guard.py status
python3 tools/codex_uwa_memory_guard.py disable
python3 tools/codex_uwa_memory_guard.py restore
```

`disable` 只保存开关原值并备份 Codex 配置，不读取或删除 memory 内容。切回官方 Codex 时可用 `restore` 恢复原值。

详细说明：`docs/CODEX_UWA_MEMORIES.md`。

## 连续性设计

项目连续性分三层：

1. Codex Desktop thread：保留客户端历史会话。
2. UWA Responses continuation：私有本地 fallback `~/.uwa/codex_responses.sqlite3`。
3. Git checkpoint：长期项目事实以仓库文档、代码、测试和提交记录为准。

私有 continuation 默认：7 天 TTL、最多 4096 条、单条最多 8 MiB；该数据库可能含 prompt、源码片段和工具输出，严禁提交。

新 thread / 新对话建议恢复顺序：

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

## 实机验收矩阵

```text
单文件读/改/测                       PASS
Stage A 多文件读/改/测                PASS
Stage B failure recovery              当前重跑目标
Stage C Git diff discipline           pending
Stage D long process + write_stdin    pending
Stage E same-thread context            pending
Stage F Codex + UWA restart continuity pending
Codex automatic Memories              isolated / future dedicated acceptance
```

独立合成工作区由 `tools/codex_desktop_acceptance.py` 创建和检查。每个 Stage 使用 `prepare -> preflight -> prompts -> check`，避免测试状态互相污染。

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

Chromium DevTools 能控制受控浏览器，严禁暴露到公网或普通局域网。

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

- 实机确认短 `exec_command(pwd)` 探针继承正确 turn cwd
- Stage B 重跑并进入 C-F
- ChatGPT Web tool-loop 增量 continuation / 会话复用
- 长上下文与 compaction
- `write_stdin` / 长进程
- auxiliary request 隔离与路由
- Codex Memories 专项支持
- MCP / namespace tools / plugins / hosted search / multi-agent

## Project history and attribution

仓库保留已有许可证与 Git commit history。当前 README、架构与验收文档描述本 fork 自己的 Codex Web Bridge 设计、实现与测试路线；历史作者署名和许可证义务继续保留。