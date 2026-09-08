# Codex Desktop D1 live PASS — 2026-09-08

## Classification

D1 is PASS.

This run used the actual Codex Desktop UI on macOS, the marked synthetic workspace `~/uwa-codex-acceptance`, and the managed UWA route.

## Machine-auditable result

The independent acceptance checker returned:

```text
multi_file: PASS
ACCEPTANCE_PASS
```

The only tracked implementation changes inside the scenario were:

```text
multi_file/math_ops.py
multi_file/summary.py
```

The test files were unchanged. The run corrected the intended arithmetic and formatting defects and the real unittest suite passed.

Python `__pycache__` directories were generated as untracked test artifacts. They were not part of the implementation diff and do not affect the gate result.

## Route proof

The post-marker route audit returned:

```text
CONFIGURED_PROVIDER=uwa
CONFIGURED_MODEL=chatgpt
CONFIGURED_EFFORT=high
LATEST_SESSION_PROVIDER=uwa
LATEST_SESSION_MODEL=chatgpt
LATEST_SESSION_EFFORT=high
CONFIG_SESSION_ROUTE=MATCH
UWA_HEALTH=healthy
UWA_BROWSER_CONNECTED=YES
UWA_WIRE_REQUEST_COUNT=4
UWA_WIRE_RESPONSE_COUNT=4
UWA_WIRE_LATEST_MODEL=chatgpt
UWA_WIRE_LATEST_EFFORT=high
UWA_WIRE_LATEST_STATUS=completed
ROUTE_EXPECTATION_PASS=YES
ROUTE_EXPECTATION_FAILURES=NONE
```

No private conversation id, account identifier, request body, command body, tool output, or local trace filename is recorded here.

## Client-tool trace proof

Metadata-only UWA wire traces in the D1 marker window showed:

```text
D1_TRACE_RESPONSE_COUNT=4
D1_TRACE_FUNCTION_CALL_NAMES=exec_command,exec_command,exec_command
D1_TRACE_EXEC_COMMAND_PRESENT=YES
D1_TRACE_COMPLETED_PRESENT=YES
D1_TRACE_METADATA_CHECK_DONE
```

This proves the Desktop turn produced real client `exec_command` function calls and a completed Responses turn. The trace mode stores metadata summaries only by default.

## Gate conclusion

All mandatory D1 conditions are satisfied:

```text
actual Desktop Codex UI used                         YES
initial synthetic fixture/preflight prepared         YES
post-run checker: multi_file: PASS                   YES
post-run checker: ACCEPTANCE_PASS                    YES
git diff --check                                     PASS
intended implementation files changed                YES
test files changed                                   NO
fresh post-marker UWA traffic                        YES
route = uwa / chatgpt / high                         YES
real exec_command function_call                      YES
completed Responses turn                             YES
```

D1 is CLOSED / PASS. The next Desktop gate is D2 same-thread continuation. D2 must use one actual Desktop thread for `context_1` followed by `context_2`, without manually repeating the hidden token.
