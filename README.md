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
真实 exec_command / native cwd         PASS
Responses tool round trip              PASS
required-tool enforcement              PASS
call-id / web-session continuation     PASS
```

Stage F 已验证真实 UWA 重启后的连续性：重启前进程内 affinity 存在，重启后 `binding_count=0`，同一 Codex thread 仍可恢复上下文并继续真实本地工具执行，最终独立 checker 返回 `ACCEPTANCE_PASS`。

## 最新 aggregate regression 状态

Stage F 收口后首次运行完整 checker：

```bash
python3 tools/codex_desktop_acceptance.py check
```

结果只有 `git_diff` 失败，其余 scenario 全部 PASS。失败详情同时显示：

```text
values_ok=True
diff_check=0
```

异常项只有 acceptance harness 自己生成或 Python 运行产生的 `PROMPTS.md`、`__pycache__`、`.pyc`。因此该结果被分类为 **harness false failure**，Stage C 的 live PASS 结论不撤销。

已完成窄范围修复：Stage C checker 现在只审计 `git_diff/` 下的 tracked diff，并继续要求唯一允许的 tracked 修改是 `git_diff/config.py`。同时已增加回归测试，确保：

1. 其他 scenario 的结果、prompt metadata、Python cache 不会污染 Stage C；
2. 修改 `git_diff/tests/*`、`REQUIREMENTS.txt` 或其他 Stage C tracked 文件仍会失败。

详细记录：

- `docs/CODEX_STAGE_F_RESTART_CONTINUITY_2026-09-07.md`
- `docs/CODEX_FULL_ACCEPTANCE_HARNESS_FALSE_FAILURE_2026-09-07.md`

## 当前推进顺序

```text
P0 修复后的完整 A-F aggregate checker 重跑
P1 large-context compaction / stress / recovery
P1 lost-affinity / restart fallback 深化验证
P1 真实项目长任务 pilot
P2 并发请求 / queue / controlled-tab 稳定性
P3 MCP / plugin namespace 与 multi-agent / tool fan-out
P4 Responses SSE slimming 与 ChatGPT Web transcript hygiene
P5 final regression / operator docs / release checklist
```

large-context 暂时不启动，先把 aggregate checker 恢复为干净 PASS。

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
