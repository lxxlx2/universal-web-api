# Codex root-workdir live diagnosis and fix

Date: 2026-09-06
Branch: `security-hardening`

## Live evidence

A clean Codex CLI probe was launched from the synthetic acceptance repository. Codex itself reported:

```text
workdir: /Users/jerson/uwa-codex-acceptance
provider: uwa
model: chatgpt
```

The user then required a real `exec_command` call containing only `pwd`. The tool result was:

```text
/
```

This proves that the Codex turn cwd was correct before the tool call, but the actual shell execution was overridden to filesystem root.

Official Codex behavior uses the turn environment cwd when `exec_command.workdir` is omitted. Therefore the observed `/` result is consistent with the web-model-generated function arguments explicitly setting `workdir: "/"`.

## Fix

The client-tool policy now treats `workdir: "/"` on `exec_command`, `shell_command`, or `local_shell` as a repairable tool-call error unless the user explicitly asked to execute from filesystem root.

Repair behavior:

1. reject the accidental root override before emitting the function call to Codex;
2. tell the web model to preserve the intended command;
3. require the corrected call to omit `workdir` entirely;
4. never guess an absolute replacement path;
5. fail closed if the model repeatedly forces root after the bounded retry budget;
6. allow `workdir: "/"` when the user explicitly requests root.

The repair system prompt also states that the Codex turn cwd is authoritative and that `/` must never be used as a default, fallback, guessed, or placeholder workdir.

## Regression coverage

`tests/test_client_tool_policy_root_workdir.py` covers:

- accidental root workdir detection for a current-workspace `pwd` probe;
- explicit root request remains allowed;
- successful internal retry from `workdir: "/"` to omitted `workdir`;
- fail-closed behavior if the web model keeps forcing root.

CI run #115 passed all jobs, including the full upstream regression job and public-repository safety checks.

## Next live probe

After pulling and restarting UWA, rerun from `~/uwa-codex-acceptance`:

```text
必须使用 exec_command 执行 pwd。
只返回该命令的真实输出，不要解释，不要推测。
```

Expected real output:

```text
/Users/jerson/uwa-codex-acceptance
```

Only after this probe passes should Stage B failure-recovery be rerun.
