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
ChatGPT Web / GPT-5.6 Sol / High
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
```

Stage F 已验证真实 UWA 重启后的连续性：重启前进程内 affinity 存在，重启后 `binding_count=0`，同一 Codex thread 仍可恢复上下文并继续真实本地工具执行，最终独立 checker 返回 `ACCEPTANCE_PASS`。

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

P1 开始前检查了当前 Codex 的 compaction transport contract。上游 Codex 在 remote compaction 时会调用：

```text
POST /v1/responses/compact
```

当前 `codex-web-bridge-v2` 的 V2、legacy Codex Responses adapter 和通用 Responses 路由代码中尚未注册这个 endpoint。P1 因此先处理 compaction 协议兼容，再生成大量 synthetic context。这样可以要求真实 `contextCompaction` 证据和压缩后的上下文恢复，而不是只验证“对话足够长”。

当前顺序：

```text
P1.0 本机 /v1/responses/compact runtime probe
P1.1 compact endpoint 实现 + regression + CI
P1.2 synthetic large-context compaction / stress / recovery
P1.3 lost-affinity / restart fallback 深化验证
P1.4 真实项目长任务 pilot
P2   并发请求 / queue / controlled-tab 稳定性
P3   MCP / plugin namespace 与 multi-agent / tool fan-out
P4   Responses SSE slimming 与 ChatGPT Web transcript hygiene
P5   final regression / operator docs / release checklist
```

详细记录：

- `docs/CODEX_STAGE_F_RESTART_CONTINUITY_2026-09-07.md`
- `docs/CODEX_FULL_ACCEPTANCE_HARNESS_FALSE_FAILURE_2026-09-07.md`
- `docs/CODEX_P1_RESPONSES_COMPACT_GAP_2026-09-07.md`

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
2. large-context 与 lost-affinity/restart recovery 无阻断问题；
3. 至少一次真实项目长任务 pilot PASS；
4. CI 全绿；
5. README、current-state、progress、operator docs、release checklist 同步；
6. public repository safety 检查通过。

## Codex Memories

UWA 验收模式继续关闭 Codex 自动 Memories：

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

## 安全边界

仓库是 public。不要提交浏览器 profile、Cookie、Local Storage、credentials、私有日志、full wire trace、Responses SQLite、真实 thread/process/browser identifiers、Codex memory workspace 内容或私有项目源码。

设计参考与许可证说明见 `docs/REFERENCES_AND_ATTRIBUTION.md`。
