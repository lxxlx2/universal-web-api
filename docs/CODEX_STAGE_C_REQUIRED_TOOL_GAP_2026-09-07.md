# Stage C required-tool wording gap — 2026-09-07

## Live result

The first Stage C `git_diff` attempt did not execute the mandatory workspace guard. The Codex turn returned:

```text
我会先严格执行工作区标记校验；只有校验通过才会读取要求、修改实现并运行测试与 diff 检查。ACCEPTANCE_WORKSPACE_MISMATCH
```

No real `exec_command` appeared in the Codex terminal output. The independent checker consequently returned:

```text
git_diff: FAIL
values_ok=False
ACCEPTANCE_FAIL count=1
```

The synthetic fixture itself remained intact; `git_diff/config.py` was simply never modified.

## Root cause

The Stage C harness wording is:

```text
第一步必须通过客户端 exec_command ...
```

The V2 required-tool detector already covered direct forms such as:

```text
必须使用 exec_command ...
```

but did not allow the explicit `客户端` token between the mandatory verb and the declared tool name. As a result, the strict required-tool contract was not activated for this harness wording, allowing a plain-text workspace mismatch claim to escape without a real probe.

## Fix

Added a compatibility detector for explicit client-prefixed Chinese forms, including:

```text
必须通过客户端 exec_command
必须使用客户端 exec_command
务必调用客户端 exec_command
```

The patch only changes required-tool language detection. It does not execute tools and does not alter Codex sandbox or approval behavior.

Regression coverage verifies the exact Stage C guard phrase and also verifies that a plain explanatory reference to `客户端 exec_command` does not force execution.

## Next live gate

Restart UWA so the new detector is loaded, then rerun the existing Stage C fixture. A passing turn must first perform the real workspace guard, then modify only `git_diff/config.py`, run tests, run `git diff --check`, and run `git diff -- git_diff`.
