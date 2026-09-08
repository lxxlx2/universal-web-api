# P1.2 remote V2 recovery: exact result with partial protocol completion

Date: 2026-09-08
Branch: `codex-web-bridge-v2`

Live rerun after enabling the UWA-only Codex `model_auto_compact_token_limit_scope = "body_after_prefix"` compatibility completed within the bounded timeout and resumed the same private Codex thread.

Observed public-safe checkpoint:

- private trace directory valid: yes
- private thread recovered: yes
- prior trigger contract: pass
- rollout compact markers before recovery: 6
- workspace token leak before recovery: no
- same thread: yes
- exact final acceptance reply: no
- client `exec_command` count: 1
- commands safe: yes
- workspace guard observed: no
- separate three-step tool protocol: no
- result referenced twice: no
- read-back observed: no
- result file exact: yes

Interpretation:

- The previous 300/900 second zero-progress compaction-thrash failure did not recur in this bounded run after the `body_after_prefix` migration.
- The exact private result file proves that the recovery turn produced the expected conversation-derived value in the workspace, but the strict acceptance protocol still failed because only one client command was observed and the mandated guard/write/read sequence was not completed.
- This checkpoint does not expose the private synthetic token, command body, thread id, local process ids, or private trace contents.
- P1.2 remains open until the single observed command is safely classified and the post-run compact marker count is checked.
