# UWA Codex Web Bridge V2

面向 Codex Desktop / Codex CLI 的本地 ChatGPT Web 推理桥。

目标是保留 Codex 的本地工作区、Shell、文件修改、测试、Git、sandbox 与 approval 能力，同时把模型推理通过本机 UWA 转发到已登录的 ChatGPT Web。网页模型负责分析和选择客户端工具，真正的本地操作仍由 Codex 客户端执行。

当前开发分支：`codex-web-bridge-v2`

## 当前状态

macOS 实机已经验证：

- 普通 ChatGPT Web 推理：PASS
- Codex custom provider：PASS
- GPT-5.6 Sol / High 目标路径：PASS
- 真实 `exec_command`：PASS
- Codex turn cwd 继承：PASS
- 单文件读 / 改 / 测：PASS
- Stage A 多文件读 / 改 / 测：PASS，checker 返回 `ACCEPTANCE_PASS`
- Responses `function_call -> function_call_output`：PASS
- V2 metadata wire trace：PASS
- 显式 required-tool contract：PASS
- duplicate required-tool suppression：PASS
- `call_id -> response_id -> ChatGPT /c/...` tool-result affinity：PASS
- V2 单次工具执行 + 单 ChatGPT Web conversation：PASS
- workspace marker/scenario probe：PASS

最新实机 workspace probe 只执行了一次真实命令，并输出：

```text
/Users/jerson/uwa-codex-acceptance
MARKER=YES
SCENARIO=YES
```

工具结果通过 call-id affinity 回到同一个 ChatGPT Web conversation，未再次执行相同命令，也未为 tool-result continuation 新建网页对话。当前下一项正式验收是 Stage B `failure_recovery`。

## 架构

```text
Codex Desktop / CLI
        ↓
OpenAI Responses request
        ↓
UWA V2 Responses guard
        ↓
previous_response_id / call_id → ChatGPT /c/... affinity
        ↓
ChatGPT Web / GPT-5.6 Sol / High
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

浏览器页面自身没有本机文件系统权限。本地文件、Shell、测试和 Git 能力来自 Codex 客户端。

## V2 Web Session Affinity

旧流程在每个外层 Responses turn 前都会准备 fresh composer，而通用 UWA workflow 默认也会执行 `new_chat_btn`。一个简单工具循环因此可能变成：

```text
用户任务
→ 新 ChatGPT 对话
→ function_call
→ Codex tool result
→ 再开新 ChatGPT 对话并重放历史
→ function_call
→ 再开新对话
```

V2 现在把网页会话连续性和 Responses 连续性绑定。正常路径使用 `previous_response_id`：

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

实机还观察到 Codex 可能以重建历史形式回传工具结果，没有可直接使用的 UWA `previous_response_id`。V2 因此增加 metadata-only call bridge：

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

1. response / call affinity 仅保存在 UWA 进程内存。
2. 映射只接受由当前受控 `chatgpt.com` 页面观测到的 `/c/...` pathname。
3. call bridge 仅保存 call id、response id 和时间戳，不保存 prompt、命令正文或 tool output。
4. continuation 复用时不重放完整 Codex transcript，只把新增 Responses delta 发到已有网页会话。
5. 已经存在匹配 `function_call + function_call_output` 时，同一个 required-tool 不会再次被强制执行。
6. Codex 浏览器轮次会临时覆盖通用 workflow 的 `new_chat` 决策，因此内部 repair round 也不会自行新开网页对话。
7. 映射丢失、TTL 到期、UWA 重启、页面不可恢复或模型/推理档不匹配时，安全回退为 `fresh chat + reconstructed history`。

默认配置：

```text
UWA_CODEX_WEB_SESSION_AFFINITY=true
UWA_CODEX_WEB_SESSION_TTL_SEC=7200
UWA_CODEX_WEB_SESSION_MAX_ENTRIES=512
```

本地只读状态接口：

```text
GET /v1/codex/web-affinity
```

只返回是否启用、binding 数量、TTL、容量和 fallback 类型，不返回 conversation pathname。

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

V2 要求 Responses 中真实出现对应 `function_call`。纯文本模拟结果、声称工具不可用、只写 `/path` 都不算成功。

首次结果没有真实工具调用时，V2 进行有限 repair。repair 使用前一次 response id 继续同一个 ChatGPT conversation。工具真实执行并有匹配 `function_call_output` 后，该 required-tool 已满足，不会因为重建历史里仍包含原始用户要求而再次强制同一工具。

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

## 连续性

项目有四个不同层次的连续性：

1. Codex Desktop thread history。
2. UWA private Responses continuation：`~/.uwa/codex_responses.sqlite3`。
3. V2 进程内 ChatGPT web-session / call-id affinity。
4. Git tracked checkpoint，作为长期项目事实来源。

V2 web affinity 丢失不会破坏项目，系统会回退 fresh chat + reconstructed Responses history。

## Codex Memories

UWA 模式当前继续关闭 Codex 自动 Memories，避免后台 memory consolidation 抢占唯一受控 ChatGPT tab：

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

## 快速开始

```bash
cd ~/universal-web-api
git switch codex-web-bridge-v2
git pull
python3 tools/codex_uwa_memory_guard.py disable
codex-uwa-stop
codex-uwa
```

基础检查：

```bash
curl -sS http://127.0.0.1:8199/health
curl -sS http://127.0.0.1:8199/v1/codex/wire-trace
curl -sS http://127.0.0.1:8199/v1/codex/web-affinity
```

## 实机验收矩阵

```text
单文件读/改/测                         PASS
Stage A 多文件读/改/测                  PASS
真实 exec_command cwd                  PASS
V2 metadata wire trace                 PASS
V2 required-tool 真 function_call       PASS
V2 单次工具执行 + 单网页会话            PASS
workspace marker/scenario probe        PASS
Stage B failure recovery               NEXT
Stage C Git diff discipline            pending
Stage D long process + write_stdin     pending
Stage E same-thread context            pending
Stage F Codex + UWA restart            pending
```

Stage B-F 通过后，还需要完成成功 Responses SSE 瘦身、网页 transcript hygiene、并发/queue/controlled-tab 稳定性、长上下文、MCP/plugin namespace、多 agent/tool fan-out、丢失 affinity fallback 和发布检查。

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

## 设计参考与 Attribution

V2 研究并借鉴了以下公开项目的设计思路：

- `lumingya/universal-web-api`：浏览器/API 基础，AGPL-3.0。
- `FlameFront-end/chatgpt-gateway`：浏览器 tool-call round trip 与结构化工具证据，MIT。
- `lininn/codex-proxy`：Responses translation 分层，MIT。
- `mehdic/codex-proxy`：sticky session、TTL、queue、SSE keepalive，MIT。
- OpenAI `codex-responses-api-proxy`：Responses 协议诊断和 paired private dumps，Apache-2.0。

详细来源、许可证、借鉴内容和差异见 `docs/REFERENCES_AND_ATTRIBUTION.md`。

当前 V2 新增代码根据这些设计原则独立实现，没有直接复制上述参考项目的源文件。仓库继续保留 upstream Git history 和既有 AGPL-3.0 许可证义务。
