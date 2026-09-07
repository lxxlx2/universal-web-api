# UWA Codex Web Bridge V2

让 Codex Desktop / Codex CLI 保留本地文件、Shell、测试、Git、sandbox 与 approval 能力，同时把模型推理通过本机 UWA 转发到已登录的 ChatGPT Web。

当前开发分支：`codex-web-bridge-v2`

## 目标

```text
Codex Desktop / CLI
        |
        | OpenAI Responses API
        v
Codex V2 guard / observability
        |
        v
UWA Codex bridge
        |
        v
受控 Chromium / ChatGPT Web
        |
        v
网页模型选择客户端工具
        |
        v
Responses function_call
        |
        v
Codex 在本机执行
        |
        v
function_call_output 返回
        |
        v
继续推理直到完成
```

网页本身不拥有本机文件系统权限。真正的文件读写、Shell、测试和 Git 操作始终由 Codex 客户端在自己的权限模型中执行。

## 当前状态

已经实机验证：

```text
普通文本推理                         PASS
单文件读取 / 修改 / 测试             PASS
Stage A 多文件读取 / 修改 / 测试      PASS
Responses function_call 交付          PASS
function_call_output 多轮继续         PASS
GPT-5.6 Sol / High 网页目标路径       PASS
```

Stage B failure-recovery 尚未完成最终实机 PASS。V2 先解决之前暴露出的协议可观测性问题，再恢复完整验收。

## 为什么拉 V2 分支

旧分支已经证明核心路线可行，但后续调试有一个明显问题：我们经常只能看到 Codex 最终显示的文字，无法马上确认它来自真实工具执行还是网页模型自己生成的文本。

例如：

```text
/
```

它可能是 `exec_command(pwd)` 的真实输出，也可能只是网页模型直接回答 `/`。

V2 的开发顺序改成：

```text
先观察 wire
-> 再强制协议约束
-> 再跑实机验收
-> 最后优化 prompt / session / 性能
```

详细设计：`docs/CODEX_WEB_BRIDGE_V2.md`。

## V2 第一批改动

### 1. 独立 Codex V2 路由层

新增：

```text
app/api/codex_responses_v2.py
```

它注册在现有 Codex Responses 路由之前。已经跑通的旧实现继续作为底层，不直接推倒重写。

这样后续可以逐步替换：

```text
Responses 兼容层
工具协议约束
wire tracing
session affinity
```

同时保留现有 UWA 浏览器控制、模型切换、网页监听和 continuation 能力。

### 2. 私有 Codex wire trace

新增：

```text
app/services/codex_wire_observability.py
```

默认写到：

```text
~/.uwa/debug/codex-wire
```

默认模式：

```text
metadata
```

metadata 只记录：

- Responses event 类型和顺序
- 是否真的出现 `function_call`
- tool name
- argument key 名称、长度和 hash
- 是否出现 `workdir` / `cwd`
- 是否等于 `/`
- response status
- request 中声明的工具名和输入规模

默认不会写入：

- prompt 正文
- 源码
- 命令正文
- tool result 正文
- Cookie / Token / Password

本地状态：

```text
GET /v1/codex/wire-trace
```

`full` 模式只用于明确的本地调试，可能包含私有源码与工具结果，严禁提交或随意分享。

### 3. Explicit required-tool contract

当用户或客户端明确要求一个已经声明的工具，例如：

```text
必须使用 exec_command 执行 pwd
```

V2 不再接受这种结果：

```text
assistant text: /
```

必须看到真实 Responses：

```text
response.output_item.done
item.type = function_call
item.name = exec_command
```

如果第一轮没有产生真实 function call，V2 会进行有限修复，并通过 `tool_choice` 强制目标函数。

仍失败时返回：

```text
required_client_tool_not_called
```

不会伪造工具输出。

## 现有保护继续保留

- GPT-5.6 Sol / High 网页模式准备与校验
- Codex minimal Responses SSE
- false local-workspace / tool-unavailable repair
- accidental `workdir="/"` guard
- `function_call_output` continuation
- 私有 SQLite Responses continuation
- UWA 模式 Codex Memories 隔离
- localhost hardened defaults
- public-repository safety rules

## 配置

新增 V2 配置：

```text
UWA_CODEX_REQUIRED_TOOL_RETRY_MAX=1
UWA_CODEX_WIRE_TRACE=metadata
UWA_CODEX_WIRE_TRACE_DIR=
UWA_CODEX_WIRE_TRACE_MAX_FILES=400
```

完整默认值见 `.env.example`。

## 本地运行

切到 V2：

```bash
cd ~/universal-web-api
git fetch origin
git switch codex-web-bridge-v2
git pull
python3 tools/codex_uwa_memory_guard.py disable
codex-uwa-stop
codex-uwa
```

基础检查：

```bash
curl -sS http://127.0.0.1:8199/health
curl -sS http://127.0.0.1:8199/v1/codex/web-mode
curl -sS http://127.0.0.1:8199/v1/codex/continuity
curl -sS http://127.0.0.1:8199/v1/codex/wire-trace
```

默认 API Base URL：

```text
http://127.0.0.1:8199/v1
```

## 下一次实机 gate

先只跑一个很短的 CLI 探针：

```text
必须使用 exec_command 执行 pwd，只返回真实命令输出。
```

通过标准必须同时满足：

```text
Codex 最终输出是正确项目目录
wire trace 中 function_call_names 包含 exec_command
```

如果网页模型只生成 `/` 之类的普通文本，V2 应该重试或明确失败，不能把它冒充成真实工具结果。

短探针通过以后，再恢复：

```text
Stage B failure recovery
Stage C Git diff discipline
Stage D long process + write_stdin
Stage E same-thread continuity
Stage F Codex + UWA restart continuity
```

## 后续技术路线

### Phase 2: tool-call prompt A/B

在同一验收集上比较现有 XML-first 和 JSON-first structured tool-call prompt。用真实合法 function-call 比率决定保留哪条路线。

### Phase 3: Responses translator isolation

进一步拆分：

```text
request normalization
backing result
Responses SSE construction
```

让协议兼容测试尽量不依赖 live browser。

### Phase 4: web-session affinity

解决当前一个 Codex agent loop 可能生成多个 ChatGPT sidebar 对话、重复灌入大段历史的问题。

目标：

```text
Codex logical session
-> stable web-session mapping
-> bounded TTL / queue
-> incremental tool-result continuation
-> mapping 丢失时回退 fresh reconstructed chat
```

## 项目连续性

长期项目状态不依赖某一个聊天窗口。

```text
Codex Desktop thread history
+ ~/.uwa 私有 continuation
+ Git 代码 / tests / docs checkpoint
```

Canonical handoff：

- `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md`
- `docs/CODEX_WEB_BRIDGE_V2.md`
- `docs/REFERENCES_AND_ATTRIBUTION.md`
- `docs/CODEX_DESKTOP_LIVE_ACCEPTANCE.md`
- `docs/CODEX_WEB_BRIDGE_PROGRESS.md`

## 安全

仓库是 public。

严禁提交：

- `.env`
- API Key / Token / Password
- Cookie / Session / Local Storage
- 浏览器 profile
- 私有 UWA / Codex 日志
- 私有源码 / prompt / tool result
- `~/.uwa/codex_responses.sqlite3`
- `~/.uwa/debug/codex-wire`
- Codex memory workspace 内容

默认 API 与 Chromium DevTools 只允许 localhost。Codex sandbox 与 approval 始终是本地执行的最终权限边界。

## 致谢与借鉴

本仓库 fork 自 `lumingya/universal-web-api`。感谢原项目作者与贡献者提供通用网页自动化、站点抽象和 OpenAI-compatible API 基础。本 fork 保留原 Git history 与 AGPL-3.0 许可证，并在此基础上发展自己的 Codex Web Bridge 路线。

V2 还研究了：

- `FlameFront-end/chatgpt-gateway`
- `lininn/codex-proxy`
- `mehdic/codex-proxy`
- OpenAI `codex-responses-api-proxy`

借鉴的具体设计、许可证与我们的差异全部记录在：

`docs/REFERENCES_AND_ATTRIBUTION.md`

当前 V2 第一批代码为独立实现，没有直接复制这些项目的源文件。以后如果实质复制或改编第三方代码，必须在对应 commit 和 attribution 文档中记录来源、上游 commit、许可证和本地目标文件。
