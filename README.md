# UWA Codex Web Bridge

一个面向本地 Codex Desktop / Codex CLI 的浏览器模型桥接实验项目。

目标：让 Codex 保留本地工作区、Shell、测试、文件修改等客户端能力，同时把推理请求通过本机 UWA 转发到已经登录的 ChatGPT 网页。网页模型负责判断和规划，真正的本地操作继续由 Codex 客户端在自己的 sandbox 与 approval 规则下执行。

当前开发分支：`security-hardening`

当前状态：Codex Desktop 普通推理已经跑通；GPT-5.6 Sol / Medium-High 网页模式锁定已经写入代码；核心本地工具循环正在做真实工作区验收。

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
Temporary Chat
+ GPT-5.6 Sol
+ Medium / High reasoning
        ↓
受控 Chromium 标签页
        ↓
网页模型决定是否调用工具
        ↓
UWA 转换为 Responses function_call
        ↓
Codex 在本机 sandbox / approval 范围内执行
        ↓
function_call_output 返回 UWA
        ↓
网页模型继续推理
```

网页页面本身不获得本机文件系统权限。`exec_command`、文件读写、测试、Git 操作等动作仍由 Codex 客户端负责。

## GPT-5.6 Sol 模式

Codex 内部仍使用逻辑路由 ID：

```text
chatgpt
```

Codex UI 中显示：

```text
GPT-5.6 Sol
```

当前只开放两个已设计映射的 reasoning 档位：

```text
Medium
High
```

默认：

```text
GPT-5.6 Sol / High
```

每次逻辑 `chatgpt` 的 Responses 请求进入 UWA 前，会先执行浏览器侧 preflight：

```text
确认/开启 Temporary Chat
↓
确认/切换 GPT-5.6 Sol
↓
确认/切换 Medium 或 High
↓
再次读取浏览器 UI 状态
↓
验证成功才继续发送请求
```

严格模式默认开启。如果 UWA 无法确认当前网页模型或 reasoning 档位，会返回 503，而不会静默降级到未知模型或未知档位。

配置：

```env
UWA_CODEX_WEB_MODE_ENABLED=true
UWA_CODEX_WEB_MODE_STRICT=true
UWA_CODEX_WEB_MODEL=GPT-5.6 Sol
UWA_CODEX_REASONING_DEFAULT=high
UWA_CODEX_TEMPORARY_CHAT=true
```

本地诊断接口：

```bash
curl http://127.0.0.1:8199/v1/codex/web-mode
```

主动应用 High：

```bash
curl -sS -X POST \
  http://127.0.0.1:8199/v1/codex/web-mode/apply \
  -H 'Content-Type: application/json' \
  -d '{"reasoning":"high"}'
```

如果返回：

```json
{
  "model": "GPT-5.6 Sol",
  "reasoning": "high",
  "temporary_chat": true,
  "verified": true
}
```

说明当前受控网页状态已经被确认。

ChatGPT 网页 DOM 会变化，因此这一层必须做真实浏览器验收。遇到 selector 变化时应该修 selector，不应该关闭 strict 模式来掩盖问题。

## 本地工具设计

UWA 负责：

- Responses / Chat Completions 协议适配
- 浏览器标签页调度
- 网页模型输入输出
- 流式响应解析
- 网页模型工具决策转译
- 工具参数校验与有限纠错
- ChatGPT Web model/reasoning preflight

Codex 负责：

- 当前工作区访问
- Shell 命令
- 文件读取与修改
- 测试执行
- sandbox
- approval
- 本机权限边界

UWA 不会为了提高兼容率主动绕过 Codex 的本地权限控制。

### 工作区误拒绝修复

已观察到真实故障：网页模型面对本地代码任务时返回“无法访问本机文件，请你自己运行这些命令”，最终没有产生 `exec_command`。

现在的策略：

```text
本地工作区任务
+ 客户端提供 exec_command / shell 工具
+ 网页模型在第一次工具调用前错误拒绝访问本机
        ↓
UWA 发送聚焦纠正提示
        ↓
要求使用客户端工具
        ↓
有限次数重试
        ↓
仍失败则 fail closed
```

如果 Codex 已经真实执行工具，并返回文件不存在、权限失败、测试失败等结果，UWA 会保留真实结果。

## 快速开始

### 获取当前开发分支

```bash
cd ~/universal-web-api
git switch security-hardening
git pull
```

### 推荐本地安全配置

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
```

启动：

```bash
python3 start.py
```

检查：

```bash
curl http://127.0.0.1:8199/health
curl http://127.0.0.1:8199/v1/codex/web-mode
```

默认 API Base URL：

```text
http://127.0.0.1:8199/v1
```

## 当前已经跑通

- hardened localhost launcher
- 独立 Chromium profile
- `/health`
- `/v1/models`
- OpenAI Chat Completions
- OpenAI Responses 非流式请求
- Responses SSE streaming
- Codex 0.153+ 模型目录格式
- Codex CLI 自定义 provider 推理
- Codex Desktop 加载 `uwa` provider
- Codex Desktop 普通文本推理
- 本地工作区误拒绝检测与重试
- 重试耗尽后的 fail-closed
- GPT-5.6 Sol model catalog 显示
- Medium / High reasoning metadata
- ChatGPT Web preflight 代码
- Temporary Chat preflight 代码
- Linux / macOS 安全回归 CI
- public repository 高置信度凭证扫描

## 当前验收目标

### 1. 网页模式验收

要求本地接口返回：

```text
model = GPT-5.6 Sol
reasoning = high
Temporary Chat = true
verified = true
```

### 2. Coding Agent 验收

最小工作区：

```python
def add(a, b):
    return a - b
```

要求 Codex Desktop 自主完成：

```text
读取 calc.py
↓
发现错误
↓
调用本地工具修改文件
↓
实际运行测试
↓
读取 function_call_output
↓
继续模型推理
↓
报告验证结果
```

通过条件：用户无需手工执行模型给出的 Shell 命令。

## 安全默认值

```text
API bind           127.0.0.1
CORS               disabled
Debug              disabled
Unsafe Python      disabled
Auto update        disabled
Remote access      disabled
DevTools           local only
Web-mode strict    enabled
```

Chromium DevTools 默认端口 `9222` 可以控制整个受控浏览器会话，严禁暴露到公网或普通局域网。

这个仓库是 public repository。禁止提交：

- `.env`
- API Key、Token、密码
- Cookie、Session、浏览器 Local Storage
- `chrome_profile/`
- UWA / Codex 私有日志
- 私有项目源码或聊天记录
- Responses 状态数据库
- 含账号、路径、密钥或私有代码的截图

详细规则见 [`SECURITY.md`](./SECURITY.md)。

## 当前限制

### ChatGPT DOM 兼容

GPT-5.6 Sol / Medium-High / Temporary Chat preflight 已经实现，但网页 DOM 可能变化。每次 ChatGPT UI 大改后需要重新做真实浏览器验收。

### Responses continuation state

当前 `previous_response_id` 相关状态主要保存在进程内存中。UWA 重启后无法保证长线程连续性。

计划加入：

```text
Git ignored
+ 本地 SQLite
+ 文件权限限制
+ TTL
+ 最大容量
+ 自动清理
+ 明确删除入口
```

### Token / context 统计

网页桥接层无法直接获得真实 API token usage。目前 Codex 中的上下文数字不能视为网页模型真实 token 计量。

计划通过本地近似计数和 32K / 64K / 96K / 128K 实测来确定保守窗口。

### 高级 Codex 能力

仍需单独验证：

- MCP
- namespace tools
- plugins
- hosted search
- multi-agent
- skills 注入
- 更复杂的 parallel tool calls

## Roadmap

```text
Phase 1  本地安全加固                          ✅
Phase 2  Codex Desktop 普通推理                 ✅
Phase 2  GPT-5.6 Sol / Medium-High preflight    代码完成，待实机验收
Phase 2  工具拒绝修复与 fail-closed             ✅
Phase 2  真实 coding-agent 工具循环             进行中
Phase 3  Responses 本地持久化                   待实现
Phase 4  Token / Context 计量                    待实现
Phase 4  MCP / Plugin / Multi-Agent              待验证
```

详细阶段记录：[`docs/CODEX_WEB_BRIDGE_PROGRESS.md`](./docs/CODEX_WEB_BRIDGE_PROGRESS.md)

## 开发与测试

```bash
python -m pytest -q tests/test_security_hardening.py
python -m pytest -q tests/test_client_tool_policy.py
python -m pytest -q tests/test_codex_compat.py
python -m pytest -q tests/test_chatgpt_web_mode.py
```

修改 Codex 兼容层、网页模式、工具调用逻辑或启动安全策略后，应等待 GitHub Actions 全部通过。

## 致谢与许可

项目沿用现有 AGPL-3.0 许可和仓库历史。感谢 `lumingya/universal-web-api` 原作者及历史贡献者提供早期浏览器桥接基础。
