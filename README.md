# UWA Codex Web Bridge V2

面向 Codex Desktop / Codex CLI 的本地 ChatGPT Web 推理桥。

当前开发分支：`codex-web-bridge-v2`。

## 项目目标

保留 Codex 的本地工作区、Shell、文件修改、测试、Git、sandbox 与 approval 能力，同时把模型推理通过本机 UWA 转发到已登录的 ChatGPT Web。网页模型负责分析与选择客户端工具，真实本地操作仍由 Codex 客户端执行。

目标使用形态：

```text
Codex Desktop / CLI
        ↓
OpenAI Responses
        ↓
UWA V2 bridge
        ↓
ChatGPT Web / GPT-5.6 Sol / High
        ↓
结构化 function_call
        ↓
Codex 本机执行文件、Shell、测试、Git
        ↓
function_call_output
        ↓
继续同一任务
```

## 当前实机进度

macOS 已验证：

- 普通 ChatGPT Web 推理：PASS
- Codex custom provider：PASS
- GPT-5.6 Sol / High：PASS
- 真实 `exec_command`：PASS
- Codex turn cwd 继承：PASS
- 单文件读 / 改 / 测：PASS
- Stage A 多文件读 / 改 / 测：PASS
- Stage B failure recovery：PASS
- Stage C Git diff discipline：PASS
- Stage D long process + `write_stdin`：PASS
- Stage E same-thread context：PASS
- Stage F restart continuity：IN PROGRESS，pre-restart turn 1 PASS
- Responses `function_call -> function_call_output`：PASS
- required-tool 真 function call：PASS
- duplicate required-tool suppression：PASS
- `call_id -> response_id -> ChatGPT conversation` continuation：PASS
- 单次工具执行 + 单网页会话：PASS

Stage E 最终实测中，两轮 Codex thread id 完全一致。第二轮没有再次提供 `EMBER-7319`，Codex 仍从同一 thread 上下文恢复令牌，真实调用本地 `exec_command`，创建并读取 `context/result.txt`，最终返回 `CONTEXT_PASS`。独立 checker 返回 `context: PASS` 和 `ACCEPTANCE_PASS`。

Stage F 已进入实机执行。重启前基线已经确认：fresh context fixture 和 preflight 均通过，新 Codex thread 第一轮返回 `CONTEXT_READY`，且 `context/result.txt` 保持不存在，因此 token 仍只存在于对话上下文。下一步将停止并重启 UWA，清除进程内 web affinity，然后通过 `codex exec resume` 恢复同一 thread，且第二轮不会再次提供 token。

详细记录：

- `docs/CODEX_STAGE_E_CONTEXT_WORKSPACE_REFUSAL_2026-09-07.md`
- `docs/CODEX_STAGE_F_RESTART_CONTINUITY_2026-09-07.md`

## 连续性设计

项目目前有四层连续性：

1. Codex Desktop / CLI thread history。
2. UWA private Responses continuation，默认保存在 `~/.uwa/codex_responses.sqlite3`。
3. V2 进程内 web-session / call-id affinity。
4. Git tracked checkpoint，作为跨对话、跨协作者的长期事实来源。

正常工具循环优先复用 `previous_response_id` 或 `call_id` 找回同一 ChatGPT Web conversation。UWA 重启后进程内 affinity 会消失，系统需要依靠持久化 Responses 历史和 Codex thread history 恢复。Stage F 专门验证这个真实长期使用场景。

## 实机验收矩阵

```text
单文件读/改/测                         PASS
Stage A 多文件读/改/测                  PASS
Stage B failure recovery               PASS
Stage C Git diff discipline            PASS
Stage D long process + write_stdin     PASS
Stage E same-thread context            PASS
Stage F Codex + UWA restart            IN PROGRESS
  turn 1 pre-restart baseline          PASS
  UWA restart                          NEXT
真实 exec_command cwd                  PASS
V2 metadata wire trace                 PASS
V2 required-tool 真 function_call       PASS
V2 单次工具执行 + 单网页会话            PASS
workspace marker/scenario probe        PASS
```

## 协作与进度同步规则

Git 是项目长期事实来源。每个 live acceptance stage、重要故障定位、关键设计改变、关键中间检查点和修复结果，在进入下一步前都要及时同步到当前开发分支。

每次至少检查并更新：

1. `README.md` 的项目思路、当前状态与下一步。
2. `docs/CODEX_WEB_BRIDGE_CURRENT_STATE.md` 的 canonical handoff。
3. `docs/CODEX_WEB_BRIDGE_PROGRESS.md` 的进度与问题链路。
4. 对应阶段的详细验收或故障记录。
5. 必要时同步 Draft PR 描述。

该规则用于保证 ChatGPT、Codex 或其他协作者即使遇到对话上下文上限，也可以只依赖 Git 恢复真实项目进度。

## Stage F 之后

核心后续工程项包括：

```text
Responses SSE payload slimming
ChatGPT Web transcript hygiene
并发请求 / queue / controlled-tab 稳定性
长上下文 stress 与 recovery
MCP / plugin namespace
multi-agent / tool fan-out
lost-affinity fallback
真实项目长任务稳定性
final regression
release checklist
```

## 合并到 main 的门槛

`codex-web-bridge-v2` 在最终验证结束前保持开发分支状态。计划在以下条件满足后合并到 `main`：

1. Stage F restart continuity 通过独立 checker。
2. Stage A 到 Stage F 最终回归通过。
3. 长上下文和 lost-affinity / restart recovery 没有阻断问题。
4. 至少完成一次真实项目长任务 pilot。
5. CI 全绿。
6. README、current-state、progress、operator docs 与 release checklist 已同步。
7. public repository safety 检查通过。

## Codex Memories

UWA 验收模式继续关闭 Codex 自动 Memories，避免后台 memory consolidation 抢占受控 ChatGPT tab：

```toml
[memories]
generate_memories = false
use_memories = false
```

## 快速启动

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

## 安全边界

默认 API 仅绑定 `127.0.0.1`。本地执行仍受 Codex sandbox 与 approval 控制。运行时日志、浏览器会话状态、Responses SQLite、wire trace、真实 thread identifier 和私有源码均不得提交到 public repository。

## 设计参考

V2 在现有 Universal Web API 基础上研究了公开项目中的 Responses adapter、browser tool round trip、sticky session、queue、SSE diagnostics 等设计。完整来源、许可证和差异记录见：

`docs/REFERENCES_AND_ATTRIBUTION.md`
