# UWA Codex Web Bridge

一个面向本地 Codex Desktop / Codex CLI 的浏览器模型桥接实验项目。

当前目标很明确：让 Codex 保留本地工作区、Shell、测试、文件修改等客户端能力，同时把推理请求通过本机 Universal Web API 转发到已经登录的网页模型。网页模型负责判断和规划，真正的本地操作继续由 Codex 客户端在自己的 sandbox 与 approval 规则下执行。

当前开发分支：`security-hardening`

当前状态：Codex Desktop 普通推理已经跑通，核心本地工具循环已经完成代码侧修复，正在做真实工作区验收。

## 我们要解决什么

常规网页 AI 可以阅读网页对话内容，却无法直接操作 Codex 当前打开的本地项目。Codex Desktop 可以访问工作区并调用本地工具，但它原生连接的是 API 模型。

这个项目把两者接起来：

```text
Codex Desktop / Codex CLI
        ↓
OpenAI Responses-compatible request
        ↓
UWA 127.0.0.1:8199
        ↓
受控 Chromium 标签页
        ↓
网页模型进行推理并决定是否调用工具
        ↓
UWA 将工具决策转换成 Responses function_call
        ↓
Codex 在本机 sandbox / approval 范围内执行
        ↓
function_call_output 返回 UWA
        ↓
网页模型继续推理
        ↓
直到任务完成
```

关键安全边界：网页页面本身不获得本机文件系统权限。`exec_command`、文件读写、测试、Git 操作等动作由 Codex 客户端负责。

## 设计原则

### 1. 本地工具由 Codex 执行

UWA 负责：

- Responses / Chat Completions 协议适配
- 浏览器标签页调度
- 网页模型输入输出
- 流式响应解析
- 网页模型工具决策转译
- 工具参数校验与有限纠错

Codex 负责：

- 当前工作区访问
- Shell 命令
- 文件读取与修改
- 测试执行
- sandbox
- approval
- 本机权限边界

UWA 不会为了提高兼容率主动绕过 Codex 的本地权限控制。

### 2. 失败要可见

我们已经观察到一种真实故障：网页模型看到本地代码任务后回复“无法访问本机文件，请你自己运行这些命令”，最终没有产生任何 `exec_command`。

现在的策略：

```text
检测到本地工作区任务
+ 客户端确实提供 exec_command / shell_command 等工具
+ 网页模型在第一次真实工具调用前错误拒绝访问本机
        ↓
发送一次聚焦纠正提示
        ↓
要求模型通过已声明客户端工具操作工作区
        ↓
有限次数重试
        ↓
仍失败则明确返回兼容失败
```

这样可以避免把“给用户一串手工命令”误报成 Codex 已经完成任务。

如果 Codex 已经真实执行了工具，并返回文件不存在、权限失败、测试失败等结果，UWA 会保留真实结果，不会继续把它当作“网页模型误拒绝”处理。

### 3. 模型身份以受控浏览器为准

Codex 里看到的 `chatgpt` 是 UWA 浏览器路由 ID。

对于 ChatGPT 网页路由，实际使用哪个网页模型由受控 Chromium 当前选中的模型决定。因此模型目录显示为：

```text
ChatGPT Web (browser-selected model)
```

路由 ID 本身不声明具体的网页模型版本。

### 4. reasoning metadata 只声明已经实现的能力

当前 Responses 请求中的 `reasoning.effort` 还没有稳定映射到网页端思考强度控件。

因此 Codex 模型目录目前只暴露一个 Web default / `medium` 占位值。`low`、`high`、`ultra` 会在真正完成网页 UI 映射之后再开放。

### 5. Public 仓库优先保证运行态隔离

这个仓库是 public repository。运行态数据必须留在本机。

禁止提交：

- `.env`
- API Key、Token、密码
- Cookie、Session、浏览器 Local Storage
- `chrome_profile/`
- UWA / Codex 私有日志
- 私有项目源码或聊天记录
- Responses 状态数据库
- 含账号、路径、密钥或私有代码的截图

详细规则见 [`SECURITY.md`](./SECURITY.md)。

## 当前已经跑通

- hardened localhost launcher
- 独立 Chromium profile
- `/health`
- `/v1/models`
- Provider 状态接口
- OpenAI Chat Completions
- OpenAI Responses 非流式请求
- Responses SSE streaming
- Codex 0.153+ `client_version` 模型目录格式
- Codex CLI 自定义 provider 推理
- Codex Desktop 加载 `uwa` provider
- Codex Desktop 普通推理
- `chatgpt` 浏览器路由模型说明
- reasoning metadata 收敛
- 本地工作区误拒绝检测
- 本地工具误拒绝聚焦重试
- 重试耗尽后的 fail-closed 行为
- Linux / macOS 安全回归 CI
- public repository 高置信度凭证扫描

## 当前验收目标

Phase 2 的真实验收用一个最小工作区完成：

```python
def add(a, b):
    return a - b
```

要求 Codex Desktop 自主完成：

```text
读取 calc.py
↓
发现 add 实现错误
↓
调用本地工具修改文件
↓
实际执行测试
↓
读取 function_call_output
↓
继续模型推理
↓
报告已经验证的结果
```

通过条件：用户无需手工执行模型给出的 Shell 命令。

## 快速开始

### 环境

建议：

- macOS
- Python 3.11 或 3.13
- Chromium / Chrome
- Codex Desktop 或 Codex CLI
- 单独的受控浏览器 Profile

### 获取当前开发分支

```bash
git clone https://github.com/lxxlx2/universal-web-api.git
cd universal-web-api
git switch security-hardening
```

已经克隆过：

```bash
cd ~/universal-web-api
git switch security-hardening
git pull
```

### 本地安全配置

推荐值：

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
```

启动：

```bash
python3 start.py
```

检查：

```bash
curl http://127.0.0.1:8199/health
curl http://127.0.0.1:8199/v1/models
```

默认 API Base URL：

```text
http://127.0.0.1:8199/v1
```

## Codex 工作方式

Codex 发来的客户端工具会被写入网页模型可理解的工具协议中。

网页模型需要调用本地工具时，UWA 将其转换为客户端可识别的 function call。真实命令仍由 Codex 执行。

典型循环：

```text
用户任务
↓
网页模型
↓
function_call: exec_command
↓
Codex 本地执行
↓
function_call_output
↓
网页模型继续
↓
下一次工具调用或最终答案
```

## 安全默认值

hardened launcher 默认采用：

```text
API bind           127.0.0.1
CORS               disabled
Debug              disabled
Unsafe Python      disabled
Auto update        disabled
Remote access      disabled
DevTools            local only
```

Chromium DevTools 默认端口 `9222` 可以控制整个受控浏览器会话，严禁暴露到公网或普通局域网。

如果未来需要通过 Tailscale 等私有网络访问，必须同时启用 API 认证、Dashboard 独立认证、强随机 Token、防火墙和明确的网络边界。

## Public 仓库 CI

当前 CI 包含：

- Ubuntu Python 3.11
- Ubuntu Python 3.13
- macOS Python 3.11
- macOS Python 3.13
- 可复现上游回归测试
- public repo safety scan

安全扫描会检查常见高置信度凭证格式和不应进入 Git 的本地运行态路径。

## 当前限制

### Responses continuation state

当前 `previous_response_id` 相关状态主要保存在进程内存中。UWA 重启后无法保证长线程连续性。

计划加入本地持久化：

```text
Git ignored
+ 本地 SQLite
+ 文件权限限制
+ TTL
+ 最大容量
+ 自动清理
+ 明确删除入口
```

该数据库可能包含源码、Prompt 和工具输出，因此实现前会先完成隐私与安全设计。

### Token / context 统计

网页桥接层无法直接获得真实 API token usage。目前 Codex 中的上下文数字不能视为网页模型真实 token 计量。

计划通过本地近似计数和 32K / 64K / 96K / 128K 实测来确定保守窗口。

### ChatGPT Memory / 历史隔离

普通登录网页可能会使用账号历史、个性化或 Memory，并产生正常聊天历史。

计划验证 Temporary Chat 工作流，让 coding agent 会话与普通账号使用尽量隔离。该功能需要根据真实网页 DOM 做稳定性测试后再加入。

### 高级 Codex 能力

当前优先目标是核心本地工具循环。

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
Phase 1  本地安全加固                     ✅
Phase 2  Codex Desktop 普通推理            ✅
Phase 2  工具拒绝修复与 fail-closed        ✅
Phase 2  真实 coding-agent 工具循环        进行中
Phase 3  Responses 本地持久化              待实现
Phase 3  Temporary Chat / Memory 隔离       待验证
Phase 4  Token / Context 计量               待实现
Phase 4  MCP / Plugin / Multi-Agent         待验证
```

详细阶段记录：[`docs/CODEX_WEB_BRIDGE_PROGRESS.md`](./docs/CODEX_WEB_BRIDGE_PROGRESS.md)

## 开发与测试

核心测试：

```bash
python -m pytest -q tests/test_security_hardening.py
python -m pytest -q tests/test_client_tool_policy.py
python -m pytest -q tests/test_codex_compat.py
```

修改 Codex 兼容层、工具调用逻辑或启动安全策略后，至少运行对应测试，并等待 GitHub Actions 全部通过。

## 致谢与许可

项目沿用现有 AGPL-3.0 许可和仓库历史。感谢 `lumingya/universal-web-api` 原作者及历史贡献者提供早期浏览器桥接基础。

当前 README、Codex Desktop 兼容设计、安全边界、工具循环修复、状态规划和后续路线均围绕本仓库当前的本地 Codex Web Bridge 目标维护。
